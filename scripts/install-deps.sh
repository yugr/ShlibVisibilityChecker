#!/bin/sh

set -eu
set -x

sudo apt-get -y install llvm libclang-dev python3 python3-setuptools python3-wheel aptitude
sudo python3 -m pip install python-magic

sudo sed -Ei 's/^# deb-src /deb-src /' /etc/apt/sources.list
sudo apt-get update
