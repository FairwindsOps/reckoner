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
                Response('stdout', 'stderr', 0, None)
            ]
            inst = provider.execute(helm_cmd)
            assert call_mock.assert_called_once
            assert isinstance(inst, HelmCmdResponse)
