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
    def setUp(self):
        self._chart = Chart(
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

    def test_caught_exceptions(self, mock_cmd_call, *args):
        """Assert that we raise the correct error if call() blows up"""
        mock_cmd_call.side_effect = [Exception('holy smokes, an error!')]
        with self.assertRaises(ReckonerCommandException):
            self._chart.run_hook('pre_install')

    @mock.patch('reckoner.chart.logging', autospec=True)
    def test_logging_info_and_errors(self, mock_logging, mock_cmd_call, *args):
        """Verify we log the right info when call() fails and succeeds"""
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
        self._chart.run_hook('pre_install')
        mock_logging.error.assert_not_called()
        mock_logging.info.assert_called()

        mock_cmd_call.side_effect = [bad_response, good_response]
        mock_logging.reset_mock()
        self._chart.run_hook('post_install')
        mock_logging.error.assert_called()
        mock_logging.info.assert_called()
        mock_logging.log.assert_called()
