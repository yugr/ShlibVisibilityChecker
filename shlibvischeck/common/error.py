# The MIT License (MIT)
# 
# Copyright (c) 2020-2022 Yury Gribov
# 
# Use of this source code is governed by The MIT License (MIT)
# that can be found in the LICENSE.txt file.

"""
Error message APIs
"""

import sys
import os.path

_except = False
_me = os.path.basename(sys.argv[0])

def warn(msg):
  "Emit nicely-formatted warning"
  sys.stderr.write(f"{_me}: warning: {msg}\n")

def error(msg):
  "Emit nicely-formatted error and abort"
  sys.stderr.write(f"{_me}: error: {msg}\n")
  if _except:
    raise RuntimeError
  sys.exit(1)

def set_basename(name):
  "Set basename for error/warning reports"
  global _me  # pylint: disable=global-statement
  _me = name

def set_throw_on_error(v=True):
  "Set behavior on error"
  global _except  # pylint: disable=global-statement
  _except = v
