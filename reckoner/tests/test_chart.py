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
import mock
from reckoner.chart import Chart, ChartResult
from reckoner.command_line_caller import Response
from reckoner.exception import ReckonerCommandException
from reckoner.yaml.handler import Handler
from io import StringIO


@mock.patch('reckoner.chart.Repository')
@mock.patch('reckoner.chart.Config')
# I have to strictly design the mock for Reckoner due to the nature of the
# key/val class setup. If the class actually had attributes then this
# would be more easily mockable
@mock.patch('reckoner.chart.call')
class TestChartHooks(unittest.TestCase):
    def get_chart(self, *args):
        chart = Chart(
            {'name': {
                'hooks': {
                    'pre_install': [
                        'omg',
                    ],
                    'post_install': [
                        'fetchez --la-vache',
                        'mooooooooo!',
                    ]
                }
            }
            },
            None,
        )
        chart.config.dryrun = False

        return chart

    def test_execution_directory(self, mock_cmd_call, *args):
        """Assert that we're executing in the same directory as the course yml"""
        _path = '/path/where/course/lives/'
        _fake_command = 'fake --command'
        chart = self.get_chart()
        chart.hooks = {
            'pre_install': [
                _fake_command
            ]
        }
        chart.config.course_base_directory = _path
        mock_cmd_call.side_effect = [Response(command_string=_fake_command, stderr='err-output', stdout='output', exitcode=0)]
        chart.run_hook('pre_install')
        mock_cmd_call.assert_called_with(_fake_command, shell=True, executable='/bin/bash', path=_path)

    def test_caught_exceptions(self, mock_cmd_call, *args):
        """Assert that we raise the correct error if call() blows up"""
        chart = self.get_chart()
        mock_cmd_call.side_effect = [Exception('holy smokes, an error!')]
        with self.assertRaises(ReckonerCommandException):
            chart.run_hook('pre_install')

    def test_raises_error_when_any_hook_fails(self, mock_cmd_call, *args):
        """Assert that we raise an error when commands fail and we don't run subsequent commands."""
        good_response = Response(
            exitcode=0,
            stderr='',
            stdout='some info',
            command_string='my --command',
        )
        bad_response = Response(
            exitcode=127,
            stderr='found exit code 127 set in test mock',
            stdout='here would be stdout',
            command_string='mock --command',
        )

        chart = self.get_chart()
        chart.hooks['pre_install'] = ['', '', '']

        mock_cmd_call.side_effect = [good_response, bad_response, good_response]

        with self.assertRaises(ReckonerCommandException):
            chart.run_hook('pre_install')

        self.assertEqual(mock_cmd_call.call_count, 2, "Call two should fail and not run the third hook.")

    @mock.patch('reckoner.chart.logging', autospec=True)
    def test_logging_info_and_errors(self, mock_logging, mock_cmd_call, *args):
        """Verify we log the right info when call() fails and succeeds"""
        chart = self.get_chart()

        # This is actually not a good test because it tightly couples the
        # implementation of logging to the test. Not sure how to do this any
        # better.
        # What I really want to test is that we're sending our info to the cli
        # user when hooks run.
        bad_response = mock.Mock(Response,
                                 exitcode=1,
                                 stderr='some error',
                                 stdout='some info',
                                 command_string='my --command')
        good_response = mock.Mock(Response,
                                  exitcode=0,
                                  stderr='',
                                  stdout='some info',
                                  command_string='my --command')
        mock_cmd_call.side_effect = [good_response]
        chart.run_hook('pre_install')
        mock_logging.error.assert_not_called()
        mock_logging.info.assert_called()

        mock_cmd_call.side_effect = [good_response, bad_response]
        mock_logging.reset_mock()
        with self.assertRaises(ReckonerCommandException):
            chart.run_hook('post_install')
        mock_logging.error.assert_called()
        mock_logging.info.assert_called()
        mock_logging.log.assert_called()

    def test_skipping_due_to_dryrun(self, mock_cmd_call, *args):
        """Verify that we do NOT run the actual calls when dryrun is enabled"""
        chart = self.get_chart()
        chart.config.dryrun = True
        chart.run_hook('pre_install')
        mock_cmd_call.assert_not_called()

    def test_hooks_support_list(self, mock_cmd_call, *args):
        """Assert that hooks can be defined as lists"""
        chart = self.get_chart()
        chart.hooks = {
            'pre_install': [
                'works',
                'twice works',
            ]
        }

        mock_cmd_call.side_effect = [
            Response(command_string='command', stderr='err-output', stdout='output', exitcode=0),
            Response(command_string='command', stderr='err-output', stdout='output', exitcode=0),
        ]
        chart.run_hook('pre_install')
        self.assertTrue(mock_cmd_call.call_count == 2)

    def test_hooks_support_strings(self, mock_cmd_call, *args):
        """Assert that hooks can be defined as a string"""
        chart = self.get_chart()
        chart.hooks = {
            'pre_install': 'works'
        }

        mock_cmd_call.side_effect = [Response(command_string='command', stderr='err-output', stdout='output', exitcode=0)]
        chart.run_hook('pre_install')
        mock_cmd_call.assert_called_once()


# @mock.patch('reckoner.chart.Repository')
# @mock.patch('reckoner.chart.Config')
# # I have to strictly design the mock for Reckoner due to the nature of the
# # key/val class setup. If the class actually had attributes then this
# # would be more easily mockable
# @mock.patch('reckoner.chart.call')
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

        with self.assertRaises(Exception):
            chart._check_env_vars()

    @mock.patch('reckoner.chart.Config', autospec=True)
    @mock.patch('reckoner.chart.os')
    def test_interpolation_of_env_vars_kube_deploy_spec(self, environMock, chartConfigMock):
        chart = Chart({'name': {'values': {}}}, None)
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False

        chart.args = ['thing=$(environVar)']
        environMock.environ = {}

        chart._check_env_vars()
        self.assertEqual(chart.args[0], 'thing=$(environVar)')

    @mock.patch('reckoner.chart.Config', autospec=True)
    @mock.patch('reckoner.chart.Repository')
    def test_chart_install(self, repositoryMock, chartConfigMock):
        repo_mock = repositoryMock()
        repo_mock.chart_path = ""
        helm_client_mock = mock.MagicMock()

        chart = Chart({'nameofchart': {'namespace': 'fakenamespace', 'set-values': {}}}, helm_client_mock)
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False

        debug_args = mock.PropertyMock(debug_args=['fake'])
        type(chart).debug_args = debug_args
        chart.install()
        helm_client_mock.upgrade.assert_called_once()
        upgrade_call = helm_client_mock.upgrade.call_args
        self.assertEqual(upgrade_call[0][0], ['nameofchart', '', '--namespace', 'fakenamespace'])

    @mock.patch('reckoner.chart.Config', autospec=True)
    @mock.patch('reckoner.chart.Repository')
    def test_chart_install_with_plugin(self, repositoryMock, chartConfigMock):
        repo_mock = repositoryMock()
        repo_mock.chart_path = ""
        helm_client_mock = mock.MagicMock()

        chart = Chart({'nameofchart': {'namespace': 'fakenamespace', 'plugin': 'someplugin', 'set-values': {}}}, helm_client_mock)
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False

        debug_args = mock.PropertyMock(debug_args=['fake'])
        type(chart).debug_args = debug_args
        chart.install()
        helm_client_mock.upgrade.assert_called_once()
        upgrade_call = helm_client_mock.upgrade.call_args
        self.assertEqual(upgrade_call[0][0], ['nameofchart', '', '--namespace', 'fakenamespace'])
        self.assertEqual(upgrade_call[1], {'plugin': 'someplugin'})


class TestChartResult(unittest.TestCase):
    def test_initialize(self):
        c = ChartResult(
            name="fake-result",
            failed=False,
            error_reason="",
        )

        assert c

    def test_string_output(self):
        c = ChartResult(name="fake-result", failed=False, error_reason="oops")
        string_output = c.__str__()
        self.assertIn("fake-result", string_output)
        self.assertIn("Succeeded", string_output)
        self.assertIn(c.error_reason, string_output)

    def test_status_string(self):
        c = ChartResult(name="railed-result", failed=True, error_reason="")
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


class TestBuildSetArguments(unittest.TestCase):
    """Test the build set args for helm chart"""

    maxDiff = None

    def setUp(self):
        self.chart_object = {
            "fake-chart": {
                "set-values": {
                    "keyone": "valueone",
                }
            }
        }

    @mock.patch('reckoner.chart.Config', autospec=True)
    def test_flat_key_values(self, chartConfigMock):
        chart = Chart(self.chart_object, None)
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False

        self.assertEqual(chart.args, [], "self.args should be empty before running")
        chart.build_set_arguments()
        self.assertEqual(chart.args, ["--set", "keyone=valueone"], "Expected build_set_arguments to build --set args correctly.")

    @mock.patch('reckoner.chart.Config', autospec=True)
    def test_dicts(self, chartConfigMock):
        chart = Chart(self.chart_object, None)
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False

        chart.set_values = {
            "levelone": {
                "leveltwo": "valuetwo",
            }
        }

        chart.build_set_arguments()
        self.assertEqual(chart.args, ["--set", "levelone.leveltwo=valuetwo"])

        chart.args = []
        chart.set_values = {
            "levelone": {
                "leveltwo": {
                    "levelthree": {
                        "levelfour": "value four",
                    }
                }
            }
        }
        chart.build_set_arguments()
        self.assertEqual(chart.args, ["--set", "levelone.leveltwo.levelthree.levelfour=value four"])

    @mock.patch('reckoner.chart.Config', autospec=True)
    def test_yaml_loaded_integration(self, chartConfigMock):
        yaml_file = StringIO('''
---
charts:
  my-chart:
    set-values:
      keyone: value one
      keytwo:
        keythree: value three
        keyfour:
        - --settings
      keyfive:
      - --one
      - --two
      deeplynested_objects:
      - name: hiya
        another:
          nested: value
          nesting: value
      - non: conforming
        lists:
        - more lists
        - and more
        - and:
            a_random_dict: value
''')
        course = Handler.load(yaml_file)
        chart = Chart(course["charts"], None)

        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False

        chart.build_set_arguments()
        self.assertEqual(chart.args, [
            "--set", "keyone=value one",
            "--set", "keytwo.keythree=value three",
            "--set", "keytwo.keyfour[0]=--settings",
            "--set", "keyfive[0]=--one",
            "--set", "keyfive[1]=--two",
            "--set", "deeplynested_objects[0].name=hiya",
            "--set", "deeplynested_objects[0].another.nested=value",
            "--set", "deeplynested_objects[0].another.nesting=value",
            "--set", "deeplynested_objects[1].non=conforming",
            "--set", "deeplynested_objects[1].lists[0]=more lists",
            "--set", "deeplynested_objects[1].lists[1]=and more",
            "--set", "deeplynested_objects[1].lists[2].and.a_random_dict=value",
        ])

    @mock.patch('reckoner.chart.Config', autospec=True)
    def test_null_value(self, chartConfigMock):
        chart = Chart(self.chart_object, None)
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False

        chart.set_values = {
            "testnull": None,
        }

        chart.build_set_arguments()
        self.assertEqual(chart.args, [
            "--set", "testnull=null",
        ])


class TestBuildSetStringsArguments(unittest.TestCase):
    """Test building of set strings"""

    def setUp(self):
        self.chart_object = {
            "fake-chart": {
                "values-strings": {
                    "keyone": "valueone",
                }
            }
        }

    @mock.patch('reckoner.chart.Config', autospec=True)
    def test_flat_key_values(self, chartConfigMock):
        chart = Chart(self.chart_object, None)
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False

        self.assertEqual(chart.args, [], "self.args should be empty before running")
        chart.build_set_string_arguments()
        self.assertEqual(chart.args, ["--set-string", "keyone=valueone"], "Expected build_set_arguments to build --set args correctly.")

    @mock.patch('reckoner.chart.Config', autospec=True)
    def test_dicts(self, chartConfigMock):
        chart = Chart(self.chart_object, None)
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False
        chart.values_strings = {
            "levelone": {
                "leveltwo": "valuetwo",
            }
        }

        chart.build_set_string_arguments()
        self.assertEqual(chart.args, ["--set-string", "levelone.leveltwo=valuetwo"])

        chart.args = []
        chart.values_strings = {
            "levelone": {
                "leveltwo": {
                    "levelthree": {
                        "levelfour": "value four",
                    }
                }
            }
        }
        chart.build_set_string_arguments()
        self.assertEqual(chart.args, ["--set-string", "levelone.leveltwo.levelthree.levelfour=value four"])

    @mock.patch('reckoner.chart.Config', autospec=True)
    def test_yaml_loaded_integration(self, chartConfigMock):
        yaml_file = StringIO('''
---
charts:
  my-chart:
    values-strings:
      keyone: value one
      keytwo:
        keythree: value three
        keyfour:
        - --settings
      keyfive:
      - --one
      - --two
      deeplynested_objects:
      - name: hiya
        another:
          nested: value
          nesting: value
      - non: conforming
        lists:
        - more lists
        - and more
        - and:
            a_random_dict: value
''')
        course = Handler.load(yaml_file)
        chart = Chart(course["charts"], None)
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False
        chart.build_set_string_arguments()
        self.assertEqual(chart.args, [
            "--set-string", "keyone=value one",
            "--set-string", "keytwo.keythree=value three",
            "--set-string", "keytwo.keyfour[0]=--settings",
            "--set-string", "keyfive[0]=--one",
            "--set-string", "keyfive[1]=--two",
            "--set-string", "deeplynested_objects[0].name=hiya",
            "--set-string", "deeplynested_objects[0].another.nested=value",
            "--set-string", "deeplynested_objects[0].another.nesting=value",
            "--set-string", "deeplynested_objects[1].non=conforming",
            "--set-string", "deeplynested_objects[1].lists[0]=more lists",
            "--set-string", "deeplynested_objects[1].lists[1]=and more",
            "--set-string", "deeplynested_objects[1].lists[2].and.a_random_dict=value",
        ])

    @mock.patch('reckoner.chart.Config', autospec=True)
    def test_null_value(self, chartConfigMock):
        chart = Chart(self.chart_object, None)
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False
        chart.values_strings = {
            "testnull": None,
        }

        chart.build_set_string_arguments()
        self.assertEqual(chart.args, [
            "--set-string", "testnull=null",
        ])
