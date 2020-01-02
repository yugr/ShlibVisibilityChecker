#!/usr/bin/python3

# The MIT License (MIT)
# 
# Copyright (c) 2020 Yury Gribov
# 
# Use of this source code is governed by The MIT License (MIT)
# that can be found in the LICENSE.txt file.

import setuptools
import os

with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r') as f:
  long_description = f.read()

setuptools.setup(
  name='shlibvischeck',
  version='0.1',
  author='Yury Gribov',
  author_email='tetra2005@gmail.com',
  description="Tool for locating internal symbols unnecessarily exported from shared libraries.",
  long_description=long_description,
  long_description_content_type='text/markdown',
  url='https://github.com/yugr/ShlibVisibilityChecker',
  packages=setuptools.find_packages(),
  scripts=['debiancheck', 'read_binary_api'],
  install_requires=['python-magic'],
  classifiers=[
    'Programming Language :: Python :: 3',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
  ],
)
