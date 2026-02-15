#!/bin/sh

# The MIT License (MIT)
# 
# Copyright (c) 2021-2026 Yury Gribov
# 
# Use of this source code is governed by The MIT License (MIT)
# that can be found in the LICENSE.txt file.

set -eu
set -x

PYTHON=${PYTHON:-python3}

sudo apt-get -y install llvm libclang-dev $PYTHON pkg-config aptitude
sudo apt-get -y install $PYTHON-pip || true
# distutils is needed by pip
sudo apt-get -y install $PYTHON-distutils || true
sudo $PYTHON -m pip install setuptools wheel python-magic

# shlibvischeck-debian needs source repos
MAJOR=$(. /etc/lsb-release && echo $DISTRIB_RELEASE | awk -F. '{print $1}')
if test $MAJOR -lt 24; then
  sudo sed -Ei 's/^# *deb-src /deb-src /' /etc/apt/sources.list
else
  sudo sed -i 's/^Types: deb$/Types: deb deb-src/g' /etc/apt/sources.list.d/ubuntu.sources
fi
sudo apt-get update
