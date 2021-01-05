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

"""Test the chart functions directly"""
import unittest
from unittest import mock

from io import StringIO

from reckoner.hooks import Hook
from reckoner.yaml.handler import Handler
from reckoner.chart import Chart, ChartResult
from reckoner.command_line_caller import Response
from reckoner.exception import ReckonerCommandException, ReckonerException

from .namespace_manager_mock import NamespaceManagerMock


class TestCharts(unittest.TestCase):
    """Test charts"""

    @mock.patch('reckoner.chart.Config', autospec=True)
    @mock.patch('reckoner.chart.os')
    def test_interpolation_of_env_vars(self, environMock, chartConfigMock):
        chart = Chart({'name': {'values': {}}}, None)
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False

        chart.args = ['thing=${environVar}', 'another=$environVar']
        environMock.environ = {'environVar': 'asdf'}

        chart._check_env_vars()
        self.assertEqual(chart.args[0], 'thing=asdf')
        self.assertEqual(chart.args[1], 'another=asdf')

    @mock.patch('reckoner.chart.Config', autospec=True)
    @mock.patch('reckoner.chart.os')
    def test_interpolation_of_missing_env_vars(self, environMock, chartConfigMock):
        chart = Chart({'name': {'values': {}}}, None)
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False

        chart.args = ['thing=${environVar}']
        environMock.environ = {}

        with self.assertRaises(Exception) as error:
            self.assertTrue(str(error).contains("Invalid placeholder"))
            chart._check_env_vars()

    @mock.patch('reckoner.chart.Config', autospec=True)
    @mock.patch('reckoner.chart.os')
    def test_interpolation_of_env_vars_kube_deploy_spec(self, environMock, chartConfigMock):
        chart = Chart({'name': {'values': {}}}, None)
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False
        chartConfig.debug = False
        chart.args = ['thing=$$(environVar)']
        environMock.environ = {}

        chart._check_env_vars()
        self.assertEqual(chart.args[0], 'thing=$(environVar)')

    @mock.patch('reckoner.chart.Config', autospec=True)
    @mock.patch('reckoner.chart.os')
    def test_interpolation_of_env_vars_raises(self, environMock, chartConfigMock):
        chart = Chart({'name': {'values': {}}}, None)
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False
        chartConfig.debug = False
        chart.args = ['thing=$(environVar)']
        environMock.environ = {}

        with self.assertRaises((ReckonerException)):
            chart._check_env_vars()

    @mock.patch('reckoner.chart.NamespaceManager', NamespaceManagerMock)
    @mock.patch('reckoner.chart.Config', autospec=True)
    @mock.patch('reckoner.chart.Repository')
    def test_chart_install(self, repositoryMock, chartConfigMock):
        repo_mock = repositoryMock()
        repo_mock.chart_path = ""
        helm_client_mock = mock.MagicMock()

        chart = Chart({'nameofchart': {'namespace': 'fakenamespace', 'values': {}}}, helm_client_mock)
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False
        chartConfig.debug = False
        chartConfig.create_namespace = True
        chartConfig.cluster_namespaces = []

        chart.install()
        helm_client_mock.upgrade.assert_called_once()
        upgrade_call = helm_client_mock.upgrade.call_args
        self.assertEqual(upgrade_call[0][0], ['nameofchart', '', '--namespace', 'fakenamespace'])

    @mock.patch('reckoner.chart.NamespaceManager', NamespaceManagerMock)
    @mock.patch('reckoner.chart.Config', autospec=True)
    @mock.patch('reckoner.chart.Repository')
    def test_chart_install_with_plugin(self, repositoryMock, chartConfigMock):
        repo_mock = repositoryMock()
        repo_mock.chart_path = ""
        helm_client_mock = mock.MagicMock()

        chart = Chart({'nameofchart': {'namespace': 'fakenamespace', 'plugin': 'someplugin', 'values': {}}}, helm_client_mock)
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False
        chartConfig.debug = False
        chartConfig.create_namespace = True
        chartConfig.cluster_namespaces = []

        chart.install()
        helm_client_mock.upgrade.assert_called_once()
        upgrade_call = helm_client_mock.upgrade.call_args
        self.assertEqual(upgrade_call[0][0], ['nameofchart', '', '--namespace', 'fakenamespace'])
        self.assertEqual(upgrade_call[1], {'plugin': 'someplugin'})

    @mock.patch('reckoner.chart.Config', autospec=True)
    def test_hooks_parsed(self, chartConfigMock):
        helm_client_mock = mock.MagicMock()
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chart = Chart({'nameofchart': {'namespace': 'fakenamespace', 'hooks': {'pre_install': 'command'},
                                       'plugin': 'someplugin', 'values': {}}}, helm_client_mock)

        self.assertIsInstance(chart.hooks, (dict))
        self.assertIsInstance(chart.pre_install_hook, (Hook))
        self.assertIsInstance(chart.post_install_hook, (Hook))

        self.assertEqual(chart.pre_install_hook.commands, ['command'])
        self.assertEqual(chart.post_install_hook.commands, [])

    @mock.patch('reckoner.chart.Config', autospec=True)
    def test_extra_config_args(self, chartConfigMock):

        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = True
        chartConfig.helm_args = ['extra', 'helm', 'args']
        chartConfig.dryrun = True

        helm_client_mock = mock.MagicMock()
        chart = Chart({'nameofchart': {'namespace': 'fakenamespace', 'hooks': {'pre_install': 'command'},
                                       'plugin': 'someplugin', 'values': {}}}, helm_client_mock)
        self.assertEqual(chart.helm_args, ['extra', 'helm', 'args'])
        self.assertEqual(chart.debug_args, ['--dry-run', '--debug'])


class TestChartResult(unittest.TestCase):

    def test_initialize(self):
        c = ChartResult(
            name="fake-result",
            failed=False,
            error_reason="",
            response=None
        )

        assert c

    def test_string_output(self):
        c = ChartResult(name="fake-result", failed=False, error_reason="oops", response=None)
        string_output = c.__str__()
        self.assertIn("fake-result", string_output)
        self.assertIn("Succeeded", string_output)
        self.assertIn(c.error_reason, string_output)

    def test_status_string(self):
        c = ChartResult(name="railed-result", failed=True, error_reason="", response=None)
        self.assertEqual(c.status_string, "Failed")
        c.failed = False
        self.assertEqual(c.status_string, "Succeeded")


class TestValuesFiles(unittest.TestCase):
    """Test the cases for provided Values Files"""

    @mock.patch('reckoner.chart.Config', autospec=True)
    def test_chart_values_file_args(self, chartConfigMock):
        """Assert that helm args include values files"""

        chart = Chart({"fake-chart": {"files": [
            "relative-file.yaml",
            "../relative-file.yaml",
            "../../relative-file.yaml",
            "path/to/nested-file.yaml",
            "/some/absolute/path/fake-file.yml"]
        }}, None)

        chart.config.dryrun = False
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '/some/fake/path'
        chartConfig.dryrun = False
        chart.build_files_list()
        self.assertEqual(chart.args, ["-f", "/some/fake/path/relative-file.yaml",
                                      "-f", "/some/fake/path/../relative-file.yaml",
                                      "-f", "/some/fake/path/../../relative-file.yaml",
                                      "-f", "/some/fake/path/path/to/nested-file.yaml",
                                      "-f", "/some/absolute/path/fake-file.yml"
                                      ])


class TestTemporaryValuesFiles(unittest.TestCase):
    """Test the cases for Temporary values files"""

    @mock.patch('reckoner.chart.Config', autospec=True)
    def test_chart_initializes_empty_file_paths(self, chartConfigMock):
        """Assert that we initialize the empty list for new charts"""
        chart = Chart({"fake-chart": {}}, None)
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False
        self.assertEqual(chart._temp_values_file_paths, [])

    @mock.patch('reckoner.chart.Config', autospec=True)
    def test_chart_creates_temp_value_files(self, chartConfigMock):
        chart = Chart({"fake-chart": {}}, None)
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False
        chart.values = {"fake-key": "fake-value"}
        self.assertEqual(len(chart._temp_values_file_paths), 0)

        chart.build_temp_values_files()
        self.assertEqual(len(chart._temp_values_file_paths), 1)

    @mock.patch('reckoner.chart.Config', autospec=True)
    @mock.patch('reckoner.chart.os', autospec=True)
    def test_remove_temp_files(self, mock_os, chartConfigMock):
        """Assert that a temp file in the list has os.remove called against it"""
        chart = Chart({"fake-chart": {}}, None)
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False
        chart._temp_values_file_paths.append('non/existent-path')
        chart.clean_up_temp_files()
        mock_os.remove.assert_called_once()
