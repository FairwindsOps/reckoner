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
        chart.run_hook('pre_install')
        mock_cmd_call.assert_called_with(_fake_command, shell=True, executable='/bin/bash', path=_path)

    def test_caught_exceptions(self, mock_cmd_call, *args):
        """Assert that we raise the correct error if call() blows up"""
        chart = self.get_chart()
        mock_cmd_call.side_effect = [Exception('holy smokes, an error!')]
        with self.assertRaises(ReckonerCommandException):
            chart.run_hook('pre_install')

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

        mock_cmd_call.side_effect = [bad_response, good_response]
        mock_logging.reset_mock()
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

        chart.run_hook('pre_install')
        self.assertTrue(mock_cmd_call.call_count == 2)

    def test_hooks_support_strings(self, mock_cmd_call, *args):
        """Assert that hooks can be defined as a string"""
        chart = self.get_chart()
        chart.hooks = {
            'pre_install': 'works'
        }

        chart.run_hook('pre_install')
        mock_cmd_call.assert_called_once()
