# The MIT License (MIT)
# 
# Copyright (c) 2020-2022 Yury Gribov
# 
# Use of this source code is governed by The MIT License (MIT)
# that can be found in the LICENSE.txt file.

"""
APIs for analyzing Debian packages
"""

import os
import os.path
import re

from shlibvischeck.common.error import error
from shlibvischeck.common.process import *
from shlibvischeck.analysis.package import *

__all__ = ['get_pkg_attribute', 'analyze_debian_package']

def _get_installed_packages():
  """ Returns installed Debian packages. """
  pkgs = set()
  _, out, _ = run('dpkg --get-selections')
  for l in out.split('\n'):
    name = re.split(r'\s+', l)[0]
    name = re.sub(r':.*', '', name)
    pkgs.add(name)
  return pkgs

def get_pkg_attribute(pkg, attr, src, last):
  """ Returns attribute of Debian package. """
  # Parse e.g. "Depends: libc6-dev | libc-dev, libacl1 (= 2.2.52-3), libattr1-dev (>= 1:2.4.46-8)"
  cmd = 'showsrc' if src else 'show'
  _, out, _ = run(f'apt-cache -q {cmd} {pkg}')
  lines = list(filter(lambda l: l.startswith(attr + ':'), out.split('\n')))
  if last:
    lines = [lines[-1]]
  vals = []
  for l in lines:
    l = re.sub(r'^[^:]*: *', '', l)
    l = re.sub(r'\([^)]*\)', '', l)
    l = l.strip()
    vals += re.split(r' *, *', l)
  return sorted(v for v in vals if v)

def _get_pkg_files(pkg):
  """ Returns list of files that belong to a package. """
  # Avoid large files and dummy /.
  _, out, _ = run(f'dpkg -L {pkg}')
  return list(filter(lambda f: not re.search(r'(\.gz|\.html?|\.)$', f),
                     out.split('\n')))

_stdinc = ['',
           '-include stdint.h -include stddef.h',
           '-include stdio.h',
           '-include sys/types.h']

def _get_cflags(files, v=0):
  """ Collect CFLAGS from pkgconfigs. """

  cflags = []

  def add_variants(f):
    for lang in ['', ' -x c++']:
      for i in range(len(_stdinc) + 1):
        cflags.append(' '.join([lang, f] + _stdinc[:i]))

  for pc in filter(lambda pkg: pkg.endswith('.pc'), files):
    stem, _ = os.path.splitext(os.path.basename(pc))
    os.environ['PKG_CONFIG_PATH'] = os.path.dirname(pc)
    _, out, _ = run(f'pkg-config --print-errors --cflags {stem}')
    out = out.strip()  # Trailing \n
    if v:
      print(f'pkg-config output:\n{out}')
    if out:
      add_variants(out)
  # In case no .pc files are present
  if not cflags:
    add_variants('')

  return cflags

def analyze_debian_package(pkg, permissive, v=0):
  """ Retuns erroneously exported private package symbolds. """

  for exe in ['aptitude', 'apt-cache', 'pkg-config']:
    if not is_runnable(exe):
      error(f"'{exe}' not installed")

  # Install all binary packages
  def is_good_package(p):
    return (not p.endswith('-udeb')
            and not p.endswith('-doc')
            and not p.endswith('-dbg')
            and 'mingw-w64' not in p)
  pkgs = get_pkg_attribute(pkg, 'Binary', True, True)
  pkgs = list(filter(is_good_package, pkgs))
  dev_pkgs = list(filter(lambda p: p.endswith('-dev'), pkgs))
  if v > 0:
    print(f"{pkg} packages: {' '.join(pkgs)}")
    print(f"{pkg} dev packages: {' '.join(dev_pkgs)}")

  installed_pkgs = _get_installed_packages()

  files = []
  for p in pkgs:  # Install single package at a time, in case some of them are missing
    if p in installed_pkgs:
      if v > 0:
        print(f"Not installing package '{p}' (already installed)")
    else:
      if v > 0:
        print(f"Installing package '{p}'...")
      # Use Aptitude to automatically resolve conflicts.
      run(f'sudo aptitude install -y -q=2 {p}')  # sudo apt-get install -qq -y $p
    files += _get_pkg_files(p)

  # TODO: use dedicated flags for files from each package
  cflags = _get_cflags(files, v)

  spurious_syms = analyze_package(pkg, files, cflags, permissive, v)
  if spurious_syms:
    print(f"The following exported symbols in package '{pkg}' are private:\n  "
          + '\n  '.join(spurious_syms))
  else:
    print(f"No private exports in package '{pkg}'")

  return True
