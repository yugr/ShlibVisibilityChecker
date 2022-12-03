[![License](http://img.shields.io/:license-MIT-blue.svg)](https://github.com/yugr/ShlibVisibilityChecker/blob/master/LICENSE.txt)
[![Build Status](https://github.com/yugr/ShlibVisibilityChecker/actions/workflows/ci.yml/badge.svg)](https://github.com/yugr/ShlibVisibilityChecker/actions)
[![codecov](https://codecov.io/gh/yugr/ShlibVisibilityChecker/branch/master/graph/badge.svg)](https://codecov.io/gh/yugr/ShlibVisibilityChecker)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/yugr/ShlibVisibilityChecker.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/yugr/ShlibVisibilityChecker/alerts/)
[![Coverity Scan](https://scan.coverity.com/projects/yugr-ShlibVisibilityChecker/badge.svg)](https://scan.coverity.com/projects/yugr-ShlibVisibilityChecker)

# What's this?

ShlibVisibilityChecker is a small tool which locates internal symbols
that are unnecessarily exported from shared libraries.
Such symbols are undesirable because they cause
* slower startup time (due to [slower relocation processing by dynamic linker](https://lwn.net/Articles/341309/), see a [real-world example](https://lore.kernel.org/lkml/CAKwvOdk0nxxUATg2jEKgx4HutXCMXcW92SX3DT+uCTgqBwQHBg@mail.gmail.com/) for Linux kernel)
* performance slowdown (due to indirect function calls, compiler's inability
  to optimize exportable functions e.g. inline them, effective turnoff of `--gc-sections`)
* leak of implementation details
  (if some clients start to use private functions instead of regular APIs)
* bugs due to runtime symbol clashing
  - [crash in Apache due to symbol clash with libasn1](https://github.com/DCIT/perl-CryptX/issues/68)
  - more real-world examples in [Flameeyes blog](https://flameeyes.blog/2008/02/09/flex-and-linking-conflicts-or-a-possible-reason-why-php-and-recode-are-so-crashy/)

ShlibVisibilityChecker compares APIs declared in public headers
against APIs exported from shared libraries and warns about discrepancies.
In majority of cases such symbols are internal library symbols which should be hidden
(in rare cases these are internal symbols which are used by other libraries or executables
in the same package and `shlibvischeck-debian` tries hard to not report such cases).

Such discrepancies should then be fixed by recompiling package
with `-fvisibility=hidden` (see [here](https://gcc.gnu.org/wiki/Visibility) for details).
A typical fix, for a typical Autoconf project can be found
[here](https://github.com/cacalabs/libcaca/issues/33#issuecomment-387656546).

ShlibVisibilityChecker _not_ meant to be 100% precise but rather provide assistance in locating packages
which may benefit the most from visibility annotations (and to understand how bad the situation
with visibility is in modern distros).

# How to use

To check a raw package, i.e. a bunch of headers and shared libs,
collect source and binary interfaces and compare them:
```
$ bin/read_header_api --only-args /usr/include/xcb/* > api.txt
$ ./read_binary_api --permissive /usr/lib/x86_64-linux-gnu/libxcb*.so > abi.txt
$ vimdiff api.txt abi.txt  # Or `comm -13 api.txt abi.txt'
```

Another useful scenario is locating symbols that are exported from
Debian package's shared libraries but are not declared in it's headers.
The main tool for this is a `shlibvischeck-debian` script.

To apply it to a package, run
```
$ shlibvischeck-debian libacl1
The following exported symbols in package 'libacl1' are private:
  __acl_extended_file
  __acl_from_xattr
  __acl_to_xattr
  __bss_start
  _edata
  _end
  _fini
  _init
  closed
  head
  high_water_alloc
  next_line
  num_dir_handles
  walk_tree
```
To skip autogenerated symbols like `_init` or `_edata` (caused by [ld linker scripts](https://sourceware.org/ml/binutils/2018-04/msg00326.html) and [libgcc startup files](https://gcc.gnu.org/ml/gcc-help/2018-04/msg00097.html)) add `--permissive`.

You can also check visibility issues in arbitrary set of headers and libraries:
```
$ shlibvischeck-common --permissive --cflags="-I/usr/include -I$AUDIT_INSTALL/include -I/usr/lib/llvm-5.0/lib/clang/5.0.0/include" $AUDIT_INSTALL/include/*.h $AUDIT_INSTALL/lib/*.so*
```

# How to install

Build-time prerequisites are `python3` (`setuptools` module), `clang`,
`llvm`, `libclang-dev`, `g++` and `make`.
Run-time dependencies are `python3` (`python-magic` module), `pkg-config` and `aptitude`.
To install everything on Ubuntu, run
```
$ sudo apt-get install python3 clang llvm libclang-dev g++ make pkg-config aptitude
$ sudo python3 -mensurepip
$ sudo pip3 install setuptools python-magic
```
(you could also use script `scripts/install-deps.sh`).

You also need to enable access to Ubuntu source packages via
```
$ sudo sed -Ei 's/^# *deb-src /deb-src /' /etc/apt/sources.list
$ sudo apt-get update
```

Python and binary components are built separately:
```
$ make clean all && make install
$ ./setup.py build && pip3 install .
```

During analysis `shlibvischeck-debian` installs new Debian packages so it's recommended to run it under chroot or in VM.
There are many instructions on setting up chroot e.g. [this one](https://github.com/yugr/debian_pkg_test).

# Where to find packages

A list of packages for analysis can be obtained from [Debian rating](https://popcon.debian.org/by_vote):
```
$ curl https://popcon.debian.org/by_vote | awk '/^[0-9]+ +lib/{print $2}' > by_vote
$ shlibvischeck-debian $(head -500 by_vote | tr '\n' ' ')
```

# How to fix a package

Once you found a problematic package, you can fix it by restricting visibility of internal symbols.
The best way to control symbol visibility in a package is to
* hide all symbols by default by adding `-fvisibility=hidden` to `CFLAGS` in project buildscripts
  (`Makefile.in` or `CMakeLists.txt`)
* explicitly annotate publicly visible functions with
  `__attribute__((visibility("default")))`

See [fix in libcaca](https://github.com/cacalabs/libcaca/pull/34/files)
for example.

# Issues and limitations

At the moment tool works only on Debian-based systems (e.g. Ubuntu).
This should be fine as buildscripts are the same across all distros
so detecting issues on Ubuntu would serve everyone else too.

An important design issue is that the tool can not detect symbols which are used indirectly
i.e. not through an API but through `dlsym` or explicit out-of-header prototype declaration
in source file. This happens in plugins or tightly interconnected shlibs within the same project.
Such cases should hopefully be rare.

ShlibVisibilityChecker is a heuristic tool so it will not be able to analyze all packages.
Current success rate is around 60%.
Major reasons for errors are
* badly-structured headers i.e. the ones which do not \#include all their dependencies 
  (e.g. `libatasmart` [fails to include `stddef.h`](https://github.com/Rupan/libatasmart/issues/1)
  and `tdb` [fails to include `sys/types.h`](https://bugzilla.samba.org/show_bug.cgi?id=13398)).
* internal headers which should not be \#included directly (e.g. `lzma/container.h`)
* experimental headers which require custom macro definitions (not listed in
  pkgconfig) (e.g. `dpkg/macros.h` requires `LIBDPKG_VOLATILE_API`)
* missing dependencies (e.g. `libverto-dev` uses Glib headers but does not declare this)

Other issues:
* TODOs are scattered all over the codebase
* would be interesting to go over dependent packages and check if they use invalid symbols

# Trophies

The tool found huge number of packages that lacked visibility annotations (in practice every second package
has spurious exports). Here are some which I tried to fix:

* Bzip2: [Hide unused symbols in libbz2](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=896750)
* Expat: [Private symbols exported from shared library](https://github.com/libexpat/libexpat/issues/195) (fixed)
* Libaudit: [Exported private symbols in audit-userspace](https://www.redhat.com/archives/linux-audit/2018-April/msg00119.html) (partially fixed)
* Gdbm: [sr #347: Add visibility annotations to hide private symbols](https://puszcza.gnu.org.ua/support/index.php?347)
* Libnfnetfilter: [\[RFC\]\[PATCH\] Hide private symbols in libnfnetlink](https://marc.info/?l=netfilter-devel&m=152481166515881) (fixed)
* Libarchive: [Hide private symbols in libarchive.so](https://github.com/libarchive/libarchive/issues/1017) ([fixed](https://github.com/libarchive/libarchive/pull/1751))
* Libcaca: [Hide private symbols in libcaca](https://github.com/cacalabs/libcaca/issues/33) (fixed)
* Libgmp: [Building gmp with -fvisibility=hidden](https://gmplib.org/list-archives/gmp-discuss/2018-April/006229.html)
* Vorbis: [Remove private symbols from Vorbis shared libs](https://github.com/xiph/vorbis/issues/43)

More perspective packages (from Debian top-100): libpopt1, libgpg-error0, libxml2, libwrap0, libpcre3, libkeyutils1, libedit2, liblcms2-2.
