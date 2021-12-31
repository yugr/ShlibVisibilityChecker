# The MIT License (MIT)
# 
# Copyright (c) 2020-2021 Yury Gribov
# 
# Use of this source code is governed by The MIT License (MIT)
# that can be found in the LICENSE.txt file.

import subprocess

from shlibvischeck.common.error import error

__all__ = ['run', 'is_runnable']

def run(cmd, fatal=True):
  """ Simple wrapper for subprocess. """

  if isinstance(cmd, str):
    cmd = cmd.split(' ')
#  print(cmd)
  p = subprocess.Popen(cmd, stdin=None, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
  out, err = p.communicate()
  out = out.decode()
  err = err.decode()
  if fatal and p.returncode != 0:
    error("'%s' failed:\n%s%s" % (' '.join(cmd), out, err))
  return p.returncode, out, err

def is_runnable(name):
  """ Check if program is present in path. """
  rc, _, _ = run([name, "--help"], fatal=False)
  return rc == 0
