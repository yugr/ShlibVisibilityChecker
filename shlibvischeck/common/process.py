# The MIT License (MIT)
# 
# Copyright (c) 2020-2022 Yury Gribov
# 
# Use of this source code is governed by The MIT License (MIT)
# that can be found in the LICENSE.txt file.

"""
APIs for handling processes
"""

import subprocess

from shlibvischeck.common.error import error

__all__ = ['run', 'is_runnable']

def run(cmd, fatal=True):
  """ Simple wrapper for subprocess. """

  if isinstance(cmd, str):
    cmd = cmd.split(' ')
#  print(cmd)
  with subprocess.Popen(cmd, stdin=None, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE) as p:
    out, err = p.communicate()
  out = out.decode()
  err = err.decode()
  if fatal and p.returncode != 0:
    error(f"'{cmd}' failed:\n{out}{err}")
  return p.returncode, out, err

def is_runnable(name):
  """ Check if program is present in path. """
  rc, _, _ = run([name, "--help"], fatal=False)
  return rc == 0
