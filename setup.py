#!/usr/bin/env python
# -- coding: utf-8 --

# Copyright 2017 Reactive Ops Inc.
#
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

from setuptools import setup, find_packages

from reckoner.meta import __version__, __author__

try:
    from setuptools import setup, find_packages
except ImportError:
    print("setup tools required. Please run: "
          "pip install setuptools).")
    sys.exit(1)


setup(name='reckoner',
      version=__version__,
      description='Declarative Helm configuration with Git capability',
      author=__author__,
      author_email='service@reactiveops.com',
      url='http://reactiveops.com/',
      license='Apache2.0',
      packages=find_packages(exclude=('tests','*.tests')),
      install_requires=[
        "click==6.7",
        "GitPython==2.1.3",
        "oyaml>=0.8",
        "coloredlogs==9.0",
        "semver==2.8.0"
      ],
      entry_points=''' #for click integration
          [console_scripts]
          reckoner=reckoner.cli:cli
      '''
      )
