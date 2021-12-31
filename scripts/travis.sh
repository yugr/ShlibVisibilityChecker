#!/bin/sh

# The MIT License (MIT)
# 
# Copyright (c) 2018-2020 Yury Gribov
# 
# Use of this source code is governed by The MIT License (MIT)
# that can be found in the LICENSE.txt file.

set -eu
set -x

make "$@" clean all
./setup.py build
./setup.py bdist_wheel
