# What's this?

ShlibVisibilityChecker is a small tool which locates private unneeded symbols
that are unnecessarily exported from shared libraries.
Such symbols are undesirable because they cause
* slower startup time (due to slower relocation processing by dynamic linker)
* performance slowdown (due to compiler's inability to optimize exportable functions e.g. inline them)
* leak of implementation details (if some clients start to use private functions instead of regular APIs)
* bugs due to unexpected runtime symbol interposition

ShlibVisibilityChecker compares APIs declared in public headers against APIs exported from shared libraries
and warns about discrepancies. Such discrepancies should then be fixed by recompiling package
with `-fvisibility=hidden` (see [here](https://gcc.gnu.org/wiki/Visibility) for details).

It's _not_ meant to be 100% precise but rather provide assistance in locating packages
which may benefit the most from visibility annotations (and to understand how bad the situation
with visibility is in modern distros).

# How to use

First install dependencies: llvm-5.0 and clang-5.0 and build as usual via `make clean all`.

To verify package, run
```
$ scripts/ifacecheck libacl1
Binary symbols not in public interface of acl:
  __acl_extended_file
  __acl_from_xattr
  __acl_to_xattr
  __bss_start
  closed
  _edata
  _end
  _fini
  head
  high_water_alloc
  _init
  next_line
  num_dir_handles
  walk_tree
For a total of 14 (25%).
```

A list of packages for analysis can be obtained from [Debian rating](https://popcon.debian.org/by_vote):
```
$ curl https://popcon.debian.org/by_vote 2>/dev/null | awk '/^[0-9]/{print $2}' | grep '^lib'
```

# Issues and limitations

ShlibVisibilityChecker is a heuristic tool so it will not be able to analyze all packages.
Current success rate is around 50%.

An important design issue is that the tool can not detect symbols which are used indirectly
i.e. not through an API but through `dlsym` or explicit out-of-header prototype declaration
in source file. This happens in plugins or tightly interconnected shlibs within the same project.
Such cases should hopefully be rare.

At the moment tool works only on Debian-based systems (e.g. Ubuntu).
This should be fine as buildscripts are the same across all distros
so detecting issues on Ubuntu would serve everyone else too.

The biggest source of errors are missing package dependencies in APT database which do not allow
installation of all dependent headers and cause preprocessing errors. This happens e.g. for `libudisks2-dev`
for which `apt-cache show` does not report dependency on `gio-2.0`).
Another common issue is that public headers are often not well-structured i.e. do not \#include
all their dependencies (e.g. `libatasmart` [fails to include `stddef.h`](https://github.com/Rupan/libatasmart/issues/1)).

Other issues:
* need to install transitive dependencies for development packages
* need to install dependencies which are mentioned in pkgconfig files (even if they are not mentioned by `apt-cache`)
* TODOs are scattered all over the codebase
* rewrite `ifacecheck` in Python/Perl (?)
* would be nice to check dependent packages to see if any uses invalid symbols
