#!/bin/sh

# Copyright 2021 Yury Gribov
#
# The MIT License (MIT)
# 
# Use of this source code is governed by MIT license that can be
# found in the LICENSE.txt file.

# This is a simple test for --only/--only-args functionality:
# function b() is not considered as belonging to libxyz interface.

set -eu

cd $(dirname $0)

if test -n "${GITHUB_ACTIONS:-}"; then
  set -x
fi

CFLAGS='-g -O2 -Wall -Wextra -Werror -shared -fPIC'

ROOT=$PWD/../..

errors=0
${CC:-gcc} $CFLAGS -shared -fPIC xyz.c -o libxyz.so
${PYTHON:-python3} $ROOT/read_binary_api --permissive libxyz.so > abi.txt

$ROOT/bin/read_header_api -r. --only xyz.h xyz.h > api.txt
(diff api.txt abi.txt || true) > api_abi.diff
if ! diff -q out.ref api_abi.diff; then
  echo >&2 "Invalid results for --only test"
  diff $name.ref api_abi.diff >&2
  errors=1
fi

$ROOT/bin/read_header_api -r. --only-args xyz.h xyz.h > api.txt
(diff api.txt abi.txt || true) > api_abi.diff
if ! diff -q out.ref api_abi.diff; then
  echo >&2 "Invalid results for --only test"
  diff $name.ref api_abi.diff >&2
  errors=1
fi

if test $errors = 0; then
  echo SUCCESS
else
  echo FAIL
fi
