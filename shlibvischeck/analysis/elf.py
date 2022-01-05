# The MIT License (MIT)
# 
# Copyright 2020-2022 Yury Gribov
# 
# Use of this source code is governed by MIT license that can be
# found in the LICENSE.txt file.

"""
APIs for analyzing ELF files
"""

import re
import subprocess

from shlibvischeck.common.process import *
from shlibvischeck.common.error import error

__all__ = ['read_binary_api']

def readelf(filename):
  """ Returns symbol table of ELF file, """

  # --dyn-syms does not always work for some reason so dump all symtabs
  with subprocess.Popen(["readelf", "-sW", filename],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
    out, err = p.communicate()
  out = out.decode()
  err = err.decode()
  if p.returncode != 0 or err:
    error("readelf failed with retcode %d: %s" % (p.returncode, err))

  toc = None
  syms = []
  for line in out.splitlines():
    line = line.strip()
    if not line:
      # Next symtab
      toc = None
      continue
    words = re.split(r' +', line)
    if line.startswith('Num'):  # Header?
      if toc is not None:
        error("multiple headers in output of readelf")
      toc = {}
      for i, n in enumerate(words):
        # Colons are different across readelf versions so get rid of them.
        n = n.replace(':', '')
        toc[i] = n
    elif toc is not None:
      sym = {k: (words[i] if i < len(words) else '') for i, k in toc.items()}
      name = sym['Name']
      if '@' in name:
        sym['Default'] = '@@' in name
        name, ver = re.split(r'@+', name)
        sym['Name'] = name
        sym['Version'] = ver
      else:
        sym['Default'] = True
        sym['Version'] = None
      syms.append(sym)

  if toc is None:
    error("failed to analyze %s" % filename)

  return syms

# These symbols are exported by nearly all shlibs
# due to bugs in older (?) GNU toolchains.
_spurious_syms = {'__bss_start', '_edata', '_init', '_fini', '_etext', '__etext', '_end'}

def read_binary_api(filename, export, disallow_spurious, v=0):
  """ Returns functions exported from shlib. """

  syms = readelf(filename)

  output_syms = []
  for s in syms:
    name = s['Name']
    ndx = s['Ndx']
    is_defined = ndx != 'UND'
    is_exported = s['Bind'] != 'LOCAL' and s['Type'] != 'NOTYPE'
    allow_versioned = not export  # If symbol is imported, we do not consider it's version
    if (name
        and ndx != 'ABS'
        and (is_defined and is_exported if export else not is_defined)
        and (not disallow_spurious or name not in _spurious_syms)
        and (s['Version'] is None or allow_versioned or s['Default'])):
      output_syms.append(name)
  output_syms = sorted(output_syms)

  if v > 0:
    print("%s symbols in %s:\n  %s"
          % ("Exported" if export else "Imported",
             filename,
             '\n  '.join(output_syms)))

  return output_syms
