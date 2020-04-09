import unittest
from unittest import mock

from reckoner.hooks import Hook
from reckoner.command_line_caller import Response
from reckoner.exception import ReckonerCommandException


@mock.patch('reckoner.hooks.call')
class TestChartHooks(unittest.TestCase):

    def test_execution_directory(self, mock_cmd_call, *args):
        """Assert that we're executing in the same directory as the course yml"""
        _path = '/path/where/course/lives/'
        _fake_command = 'fake --command'
        _hook = Hook(_fake_command, 'test_execution_directory_hook', _path)
        mock_cmd_call.side_effect = [Response(command_string=_fake_command, stderr='err-output', stdout='output', exitcode=0)]
        _hook.run()
        mock_cmd_call.assert_called_with(_fake_command, shell=True, executable='/bin/bash', path=_path)

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

        _hook = Hook(['', '', ''], "test_raises_error_when_any_hook_fails", '')

        mock_cmd_call.side_effect = [good_response, bad_response, good_response]

        with self.assertRaises(ReckonerCommandException):
            _hook.run()

        self.assertEqual(mock_cmd_call.call_count, 2, "Call two should fail and not run the third hook.")


    def test_hooks_support_list(self, mock_cmd_call, *args):
        """Assert that hooks can be defined as lists"""
        _hook = Hook([
            'works',
            'twice works',
        ], 'test_hooks_support_list')

        mock_cmd_call.side_effect = [
            Response(command_string='command', stderr='err-output', stdout='output', exitcode=0),
            Response(command_string='command', stderr='err-output', stdout='output', exitcode=0),
        ]
        _hook.run()
        self.assertTrue(mock_cmd_call.call_count == 2)

    def test_hooks_support_strings(self, mock_cmd_call, *args):
        """Assert that hooks can be defined as a string"""
        _hook = Hook('works', 'test_hooks_support_strings')

        mock_cmd_call.side_effect = [Response(command_string='command', stderr='err-output', stdout='output', exitcode=0)]
        _hook.run()
        mock_cmd_call.assert_called_once()
