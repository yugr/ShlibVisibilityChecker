# The MIT License (MIT)
# 
# Copyright (c) 2020 Yury Gribov
# 
# Use of this source code is governed by The MIT License (MIT)
# that can be found in the LICENSE.txt file.

import sys
import os.path

_except = False
_me = os.path.basename(sys.argv[0])

def warn(msg):
  sys.stderr.write("%s: warning: %s\n" % (_me, msg))

def error(msg):
  sys.stderr.write("%s: error: %s\n" % (_me, msg))
  global _except
  if _except:
    raise RuntimeError
  sys.exit(1)

def set_basename(name):
  global _me
  _me = name

def set_throw_on_error(v=True):
  global _except
  _except = v
