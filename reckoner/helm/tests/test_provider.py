# Intent for this file is to be able to contract test ALL providers!
import unittest
import mock
from reckoner.helm.provider import HelmProvider
from reckoner.helm.cmd_response import HelmCmdResponse
from reckoner.helm.command import HelmCommand
from reckoner.command_line_caller import Response


@mock.patch('reckoner.helm.provider.call')
class TestAllProviders(unittest.TestCase):
    def setUp(self):
        self._list_of_providers = [
            HelmProvider,
        ]

    def test_execute_contract(self, call_mock):
        """Expect all the providers to accept a specific method signature and output correct object"""
        for provider in self._list_of_providers:
            helm_cmd = HelmCommand('mocking-helm', ['--debug'])
            call_mock.side_effect = [
                Response('stdout', 'stderr', 0)
            ]
            inst = provider.execute(helm_cmd)
            assert call_mock.assert_called_once
            assert isinstance(inst, HelmCmdResponse)
