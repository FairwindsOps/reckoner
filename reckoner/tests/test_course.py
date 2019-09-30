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

import mock
import unittest
from reckoner.course import Course
from reckoner.command_line_caller import Response
from reckoner.helm.client import HelmClientException
from reckoner.exception import ReckonerException


@mock.patch('reckoner.repository.Repository', autospec=True)
@mock.patch('reckoner.course.sys')
@mock.patch('reckoner.course.yaml_handler', autospec=True)
@mock.patch('reckoner.course.get_helm_client', autospec=True)
@mock.patch('reckoner.course.Config', autospec=True)
class TestMinVersion(unittest.TestCase):
    def test_init_error_fails_min_version_reckoner(self, configMock, helmClientMock, yamlLoadMock, sysMock, repoMock):
        """Tests that minimum version will throw an exit."""
        c = configMock()
        c.helm_args = ['provided args']

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

        Course(None)

        sysMock.exit.assert_called_once
        return True

    def test_init_error_fails_min_version_helm(self, configMock, helmClientMock, yamlLoadMock, sysMock, repoMock):
        """Tests that minimum version will throw an exit."""
        c = configMock()
        c.helm_args = ['provided args']

        h = helmClientMock(c.helm_args)
        h.version = '0.0.1'

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

        Course(None)

        sysMock.exit.assert_called_once
        return True


class TestIntegrationWithChart(unittest.TestCase):
    @mock.patch('reckoner.chart.Config', autospec=True)
    @mock.patch('reckoner.chart.call', autospec=True)
    @mock.patch('reckoner.repository.Repository', autospec=True)
    @mock.patch('reckoner.course.sys')
    @mock.patch('reckoner.course.yaml_handler', autospec=True)
    @mock.patch('reckoner.course.get_helm_client', autospec=True)
    @mock.patch('reckoner.course.Config', autospec=True)
    def test_failed_pre_install_hooks_fail_chart_installation(self, configMock, helmClientMock, yamlLoadMock, sysMock, repoMock, chartCallMock, chartConfigMock):
        """Test that the chart isn't installed when the pre_install hooks return any non-zero responses. This also assures we don't raise python errors with hook errors."""
        c = configMock()
        # TODO Fix how this mock is autospecced - something fishy with having this class attribs all come from dict options
        c.continue_on_error = False
        c.helm_args = ['provided args']
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False
        h = helmClientMock(c.helm_args)
        h.client_version = '0.0.1'

        yamlLoadMock.load.return_value = {
            'charts': {
                'first-chart': {
                    'hooks': {
                        'pre_install': [
                            'run a failed command here',
                        ]
                    }
                }
            }
        }

        chartCallMock.return_value = Response(exitcode=1, command_string='mocked', stderr=' ', stdout=' ')

        course = Course(None)
        results = course.plot(['first-chart'])

        self.assertEqual(chartCallMock.call_count, 1)
        self.assertEqual(len([result for result in results if result.failed]), 1, "We should have only one failed chart install due to hook failure.")


@mock.patch('reckoner.course.yaml_handler', autospec=True)
@mock.patch('reckoner.course.get_helm_client', autospec=True)
class TestCourse(unittest.TestCase):
    def setUp(self):
        self.course_yaml = {
            'charts': {
                'first-chart': {
                    'repository': 'stable',
                    'chart': 'nonexistant',
                    'version': '0.0.0',
                }
            }
        }

    def test_plot(self, mockGetHelm, mockYAML):
        mockYAML.load.return_value = self.course_yaml
        course = Course(None)
        assert course.plot(['first-chart'])

    def test_str_output(self, mockGetHelm, mockYAML):
        mockYAML.load.return_value = self.course_yaml
        assert Course(None).__str__()

    def test_chart_install_logic(self, mockGetHelm, mockYAML):
        mockYAML.load.return_value = {
            'charts': {
                'first-chart': {},
                'second-chart': {}
            }
        }

        # expect the first chart install to bubble up an error
        chart = mock.MagicMock()
        chart.result = None
        chart.install.side_effect = Exception("Second command has an error")

        course = Course(None)
        self.assertEqual(len(course.install_charts([chart, chart])), 1)

        course.config.continue_on_error = True
        self.assertEqual(len(course.install_charts([chart, chart])), 2)

    def test_course_raises_errors_on_bad_client_response(self, mockGetHelm, mockYAML, *args):
        """Make sure course wraps get_helm_client exceptions as ReckonerExceptions"""
        # Load the course "yaml"
        mockYAML.load.return_value = self.course_yaml

        # Check helm client exception checking command
        mockGetHelm.side_effect = HelmClientException('broken')
        with self.assertRaises(ReckonerException):
            Course(None)
        mockGetHelm.assert_called_once()
        mockGetHelm.reset_mock()

        mockGetHelm.side_effect = Exception("it's a mock: had an error starting helm client")
        with self.assertRaises(ReckonerException):
            Course(None)

# TODO: Add test for calling plot against a chart that doesn't exist in your course.yml
