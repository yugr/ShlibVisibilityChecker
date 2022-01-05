# The MIT License (MIT)
# 
# Copyright 2020-2022 Yury Gribov
# 
# Use of this source code is governed by MIT license that can be
# found in the LICENSE.txt file.

"""
APIs for analyzing C headers
"""

import os
import os.path
import re

from shlibvischeck.common.process import *
from shlibvischeck.common.error import error

__all__ = ['read_header_api']

def read_header_api(hdr, whitelist, cflags, v=0):
  """ Returns functions declared in header
      (and included headers from whitelist). """

  if not cflags:
    cflags = ['']

  # Is this a helper header and so not intended for direct inclusion?
  is_helper = 'private' in hdr  # E.g. json_object_private.h
  hdr_base = os.path.basename(hdr)
  for filename in whitelist:
    with open(filename) as f:
      txt = f.read()
      if re.search(fr'^\s*#\s*include\s+[<"].*{hdr_base}[>"]', txt, re.M):
        is_helper = True

  errors = []
  syms = []

  for f in cflags:
    cmd = ['read_header_api', '--only', ' '.join(whitelist), '--cflags', f, hdr]
    rc, out, err = run(cmd, fatal=False)
    if rc == 0:
      syms = out.split('\n')
      break
    errors.append((' '.join(cmd), out, err))

  if not syms and not is_helper:
    msgs = ["failed to parse:"]
    for cmd, out, err in errors:
      msgs.append(f"compiling '{cmd}':")
      msgs.append(err)
    error('\n'.join(msgs))

  if v > 0 and syms:
    print("Public functions in header %s:\n  %s"
          % (hdr, '\n  '.join(syms)))

  return syms
