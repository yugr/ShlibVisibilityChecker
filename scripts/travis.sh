#!/bin/sh

# The MIT License (MIT)
# 
# Copyright (c) 2018-2021 Yury Gribov
# 
# Use of this source code is governed by The MIT License (MIT)
# that can be found in the LICENSE.txt file.

set -eu
set -x

# Build

make "$@" clean all
./setup.py build
./setup.py bdist_wheel

# Run tests

test/basic/run.sh
test/debian/run.sh
test/only/run.sh

# Upload coverage
if test -n "${CODECOV_TOKEN:-}"; then
  for t in tests/*; do
    if test -d $t; then
      (cd $t && coverage xml)
    fi
  done
  curl --retry 5 -s https://codecov.io/bash > codecov.bash
  bash codecov.bash -Z
  find -name \*.gcda -o -name \*.gcno -o -name \*.gcov -o -name \*.xml | xargs rm
fi
