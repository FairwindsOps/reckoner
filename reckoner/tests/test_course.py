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

import mock
import unittest
from reckoner.exception import MinimumVersionException
from reckoner.course import Course


@mock.patch('reckoner.repository.Repository', autospec=True)
@mock.patch('reckoner.course.sys')
@mock.patch('reckoner.course.yaml', autospec=True)
@mock.patch('reckoner.course.HelmClient', autospec=True)
@mock.patch('reckoner.course.Config', autospec=True)
class TestMinVersion(unittest.TestCase):
    def test_init_error_fails_min_version_reckoner(self, configMock, helmClientMock, yamlLoadMock, sysMock, repoMock):
        """Tests that minimum version will throw an exit."""
        c = configMock()
        c.helm_args = ['provided args']
        c.local_development = False

        yamlLoadMock.load.return_value = {
            'repositories': {
                'name': {},
            },
            'helm_args': None,
            'minimum_versions': {
                'reckoner': '1000.1000.1000',  # minimum version needed
                # find the version of reckoner at meta.py __version__
            }
        }

        sysMock.exit.return_value = None

        course = Course(None)

        sysMock.exit.assert_called_once
        return True

    def test_init_error_fails_min_version_helm(self, configMock, helmClientMock, yamlLoadMock, sysMock, repoMock):
        """Tests that minimum version will throw an exit."""
        c = configMock()
        c.helm_args = ['provided args']
        c.local_development = False

        h = helmClientMock()
        h.client_version = '0.0.1'

        yamlLoadMock.load.return_value = {
            'repositories': {
                'name': {},
            },
            'helm_args': None,
            'minimum_versions': {
                'helm': '1000.1000.1000',  # minimum version needed
            }
        }

        sysMock.exit.return_value = None

        course = Course(None)

        sysMock.exit.assert_called_once
        return True
