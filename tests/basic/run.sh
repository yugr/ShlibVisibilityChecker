#!/bin/sh

# Copyright 2021-2022 Yury Gribov
#
# The MIT License (MIT)
# 
# Use of this source code is governed by MIT license that can be
# found in the LICENSE.txt file.

# This is a simple test for ShlibVisibilityChecker functionality.

set -eu

cd $(dirname $0)

if test -n "${GITHUB_ACTIONS:-}"; then
  set -x
fi

CFLAGS='-g -O2 -Wall -Wextra -Werror -shared -fPIC'

ROOT=$PWD/../..

$ROOT/bin/read_header_api -r. xyz.h > api.txt

errors=0
for name_flags in 'a;-DA' 'b;-DB' 'ab;-DA -DB'; do
  name=${name_flags%;*}
  flags=${name_flags#*;}

  ${CC:-gcc} $CFLAGS $flags -shared -fPIC xyz.c -o libxyz.so
  ${PYTHON:-python3} $ROOT/read_binary_api --permissive libxyz.so > abi.txt

  (comm -3 api.txt abi.txt || true) > api_abi.diff
  if ! diff -q $name.ref api_abi.diff; then
    echo >&2 "Invalid results for test $name"
    diff $name.ref api_abi.diff >&2
    errors=1
  fi
done

if test $errors = 0; then
  echo SUCCESS
else
  echo FAIL
fi
