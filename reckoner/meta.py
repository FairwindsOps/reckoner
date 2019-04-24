# -- coding: utf-8 --

# pylint: skip-file

# Copyright 2019 ReactiveOps Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from pkg_resources import get_distribution, DistributionNotFound
import re

__version_modifier__ = re.compile(r'^([0-9]+\.[0-9]+\.[0-9]+)\.(.*)$')
__distribution_name__ = 'reckoner'
try:
    __version__ = re.sub(__version_modifier__, r'\g<1>-\g<2>', get_distribution(__distribution_name__).version)
except DistributionNotFound:
    # Attempt to discover Version from pyinstaller data
    from pkgutil import get_data
    _raw_ver = get_data(__distribution_name__, 'version.txt').decode('UTF-8', 'ignore').rstrip("\r\n")
    __version__ = re.sub(__version_modifier__, r'\g<1>-\g<2>', _raw_ver)
__author__ = 'ReactiveOps, Inc.'
