#!/bin/sh

# Copyright 2021 Yury Gribov
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

T=$PWD
ROOT=$T/../..
PATH=$ROOT/bin:$PATH

PKGS=libbz2-1.0

errors=0
for pkg in $PKGS; do
  (cd $ROOT && ./shlibvischeck-debian $pkg) > out.log

  if ! diff -q $pkg.ref out.log; then
    echo >&2 "Invalid results for package"
    diff $pkg.ref out.log >&2
    errors=1
  fi
done

if test $errors = 0; then
  echo SUCCESS
else
  echo FAIL
fi
