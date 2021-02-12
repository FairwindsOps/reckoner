# Copyright 2019 FairwindsOps Inc
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

from reckoner.importer import get_values, list_release
import unittest
from unittest import mock
from reckoner.importer import draft_release
from reckoner.command_line_caller import Response


@mock.patch('reckoner.importer.get_values')
@mock.patch('reckoner.importer.list_release')
class TestDraftRelease(unittest.TestCase):
    """Test importer.draft_release"""

    def test_basic_import(self, mock_values, mock_release):
        """Assure we fail when NoChartsToInstall is bubbled up"""
        mock_release.return_value = {"test_value_one": "one_value_test"}
        mock_values.return_value = {"chart": "test-chart-1.0.0"}

        chart_block = draft_release('test-release',
                                    'test-namespace',
                                    'test-repository'
                                    )

        self.assertEqual(
            chart_block,
            {'test-release': {'chart': 'test',
                              'namespace': 'test-namespace',
                              'repository': 'test-repository',
                              'values': {'test_value_one': 'one_value_test'},
                              'version': '1.0.0'}}
        )

    def test_basic_import(self, mock_values, mock_release):
        """Assure we fail when NoChartsToInstall is bubbled up"""
        mock_release.return_value = {"test_value_one": "one_value_test"}
        mock_values.return_value = {"chart": "test-chart-1.0.0"}

        chart_block = draft_release('test-release',
                                    'test-namespace',
                                    'test-repository'
                                    )

        self.assertEqual(
            chart_block,
            {'test-release': {'chart': 'test-chart',
                              'namespace': 'test-namespace',
                              'repository': 'test-repository',
                              'values': {'test_value_one': 'one_value_test'},
                              'version': '1.0.0'}}
        )


@mock.patch('reckoner.importer.get_helm_client')
class TestHelmFunctions(unittest.TestCase):
    def test_get_values(self, mock_helm_client):
        h = mock_helm_client()
        h.get_values.return_value = Response(
            '{"test1":"test-value-1","test2":{"test3":"test-value-3"}}',
            '',
            0,
            ''
        )

        values = get_values('test-release',
                            'test-namespace')
        self.assertEqual(
            {
                'test1': 'test-value-1',
                'test2': {
                    'test3': 'test-value-3'
                }
            },
            values
        )

    def test_list_release(self, mock_helm_client):
        h = mock_helm_client()
        h.list_releases.return_value = Response(
            '[{"name":"test-release","chart":"test-chart-1.0.0"}]',
            '',
            0,
            ''
        )

        release = list_release('test-release',
                               'test-namespace')
        self.assertEqual({'name': 'test-release', 'chart': 'test-chart-1.0.0'}, release)
