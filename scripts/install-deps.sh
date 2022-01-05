#!/bin/sh

# The MIT License (MIT)
# 
# Copyright (c) 2021 Yury Gribov
# 
# Use of this source code is governed by The MIT License (MIT)
# that can be found in the LICENSE.txt file.

set -eu
set -x

sudo apt-get -y install llvm libclang-dev python3 python3-pip aptitude
sudo python3 -m pip install setuptools wheel python-magic

# shlibvischeck-debian needs source repos
sudo sed -Ei 's/^# deb-src /deb-src /' /etc/apt/sources.list
sudo apt-get update
