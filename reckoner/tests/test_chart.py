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

"""Test the chart functions directly"""
import unittest
import mock
from reckoner.chart import Chart
from reckoner.command_line_caller import Response
from reckoner.exception import ReckonerCommandException


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
        chart.config.local_development = False

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

    def test_skipping_due_to_local_development(self, mock_cmd_call, *args):
        """Verify skipping call() when in local_development"""
        chart = self.get_chart()

        chart.config.local_development = True
        chart.run_hook('pre_install')
        mock_cmd_call.assert_not_called()

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

    @mock.patch('reckoner.chart.os')
    def test_interpolation_of_env_vars(self, environMock):
        chart = Chart({'name': {'values': {}}}, None)
        chart.config.dryrun = False
        chart.config.local_development = False

        chart.args = ['thing=${environVar}', 'another=$environVar']
        environMock.environ = {'environVar': 'asdf'}

        chart._check_env_vars()
        self.assertEqual(chart.args[0], 'thing=asdf')
        self.assertEqual(chart.args[1], 'another=asdf')

    @mock.patch('reckoner.chart.os')
    def test_interpolation_of_missing_env_vars(self, environMock):
        chart = Chart({'name': {'values': {}}}, None)
        chart.config.dryrun = False
        chart.config.local_development = False

        chart.args = ['thing=${environVar}']
        environMock.environ = {}

        with self.assertRaises(Exception):
            chart._check_env_vars()

    @mock.patch('reckoner.chart.os')
    def test_interpolation_of_env_vars_kube_deploy_spec(self, environMock):
        chart = Chart({'name': {'values': {}}}, None)
        chart.config.dryrun = False
        chart.config.local_development = False

        chart.args = ['thing=$(environVar)']
        environMock.environ = {}

        chart._check_env_vars()
        self.assertEqual(chart.args[0], 'thing=$(environVar)')
