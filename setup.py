#!/usr/bin/env python
# -- coding: utf-8 --

# Copyright 2017 FairwindsOps Inc.
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

import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    print("setup tools required. Please run: "
          "pip install setuptools).")
    sys.exit(1)


setup(name='reckoner',
      python_requires='>=3.7',
      use_scm_version=True,
      setup_requires=['setuptools_scm'],
      description='Declarative Helm configuration with Git capability',
      author='FairwindsOps Inc.',
      author_email='service@fairwinds.com',
      url='https://fairwinds.com/',
      license='Apache2.0',
      packages=find_packages(exclude=('tests', '*.tests')),
      include_package_data=True,
      install_requires=[
          "click==7.1.2",
          "GitPython>=2.1.11",
          "coloredlogs>=9.0",
          "semver>=2.8.1",
          "ruyaml>=0.20.0",
          "jsonschema>=3.0.2",
          "kubernetes==12.0.1",
          "boto3==1.18.15"
      ],
      entry_points=''' #for click integration
          [console_scripts]
          reckoner=reckoner.cli:cli
      '''
      )
