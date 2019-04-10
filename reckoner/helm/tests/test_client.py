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

from reckoner.helm.client import HelmClient, HelmClientException
from reckoner.helm.command import HelmCommand
from reckoner.helm.cmd_response import HelmCmdResponse
import mock
import unittest


class TestHelmClient(unittest.TestCase):
    def setUp(self):
        self.dummy_provider = mock.Mock()

    def test_default_helm_arguments(self):
        helm_client = HelmClient(provider=self.dummy_provider)
        assert hasattr(helm_client, 'default_helm_arguments')

    def test_server_version(self):
        self.dummy_provider.execute.return_value = HelmCmdResponse(0, '', 'Server: v0.0.0+gabcdef01234', '')
        assert '0.0.0' == HelmClient(provider=self.dummy_provider).server_version

    def test_client_version(self):
        self.dummy_provider.execute.return_value = HelmCmdResponse(0, '', 'Client: v0.0.0+gabcdef01234', '')
        assert '0.0.0' == HelmClient(provider=self.dummy_provider).client_version

    def test_public_methods(self):
        helm_client = HelmClient(provider=self.dummy_provider)
        methods = [
            'execute',
            'check_helm_command',
            'upgrade',
        ]

        for method in methods:
            assert hasattr(helm_client, method)

    def test_repositories(self):
        repositories_string = """NAME            URL
stable          https://kubernetes-charts.storage.googleapis.com
local           http://127.0.0.1:8879/charts
test_repo       https://kubernetes-charts.storage.googleapis.com
incubator       https://kubernetes-charts-incubator.storage.googleapis.com"""

        repositories_expected = ['stable', 'local', 'test_repo', 'incubator']

        self.dummy_provider.execute.return_value = HelmCmdResponse(
            0,
            '',
            repositories_string,
            '',
        )

        assert HelmClient(provider=self.dummy_provider).repositories == repositories_expected

        repositories_string_extra_lines = """
NAME            URL
stable          https://kubernetes-charts.storage.googleapis.com
local           http://127.0.0.1:8879/charts

test_repo       https://kubernetes-charts.storage.googleapis.com
incubator       https://kubernetes-charts-incubator.storage.googleapis.com

"""
        self.dummy_provider.execute.return_value = HelmCmdResponse(
            0,
            '',
            repositories_string_extra_lines,
            ''
        )

        assert HelmClient(provider=self.dummy_provider).repositories == repositories_expected

    def test_execute_with_additional_parameters(self):
        default_params = ['--some params']
        adhoc_params = ['--some more']
        expected_params = default_params + adhoc_params

        HelmClient(
            default_helm_arguments=default_params,
            provider=self.dummy_provider
        ).execute('version', adhoc_params)

        assert self.dummy_provider.execute.call_args[0][0].arguments == expected_params

    def test_execute_with_default_helm_arguments(self):
        expected_params = ['--some params', '--found']
        helm_client = HelmClient(provider=self.dummy_provider)
        helm_client.default_helm_arguments = expected_params

        helm_client.execute('help')

        self.dummy_provider.execute.assert_called_once
        assert isinstance(self.dummy_provider.execute.call_args[0][0], HelmCommand)
        assert self.dummy_provider.execute.call_args[0][0].arguments == expected_params

    def test_check_helm_command(self):
        self.dummy_provider.execute.side_effect = [
            HelmCmdResponse(0, None, None, None),
            HelmCmdResponse(127, None, None, None)
        ]
        assert HelmClient(provider=self.dummy_provider).check_helm_command() == True
        with self.assertRaises(HelmClientException) as e:
            assert HelmClient(provider=self.dummy_provider).check_helm_command() == False

    def test_upgrade(self):
        self.dummy_provider.execute.side_effect = [
            HelmCmdResponse(
                0, '', 'pass', HelmCommand('install', ['--install'])
            ),
            HelmCmdResponse(
                0, '', 'pass', HelmCommand('install', [])
            )
        ]

        with_install = HelmClient(provider=self.dummy_provider).upgrade([], install=True)
        without_install = HelmClient(provider=self.dummy_provider).upgrade([], install=False)

        assert with_install.command.arguments == ['--install']
        assert without_install.command.command == 'install'
        assert with_install.command.arguments == ['--install']
        assert without_install.command.command == 'install'

    def test_dependency_update(self):
        HelmClient(provider=self.dummy_provider).dependency_update('chart_path')
        self.dummy_provider.execute.assert_called_once

    def test_repo_update(self):
        HelmClient(provider=self.dummy_provider).repo_update()
        self.dummy_provider.execute.assert_called_once

    def test_verify_default_helm_args_intantiate(self):
        # Should support instantiate with None
        assert HelmClient(provider=self.dummy_provider, default_helm_arguments=None)

        # Should raise errors on all other non iterators
        for invalid in [str('invalid'), 1, 0.01, True]:
            with self.assertRaises(ValueError):
                HelmClient(default_helm_arguments=invalid)

    def test_repo_add(self):
        HelmClient(provider=self.dummy_provider).repo_add('new', 'url')
        self.dummy_provider.execute.assert_called_once

    def test_version_regex(self):
        invalid = [
            'not valid',
            'Client:v0.0.0+asdf',
            '938: v0.0.0+g9ada0993'
            ': v0.010.0',
        ]

        valid = [
            ('Client: v0.0.0+gaaffed92', '0.0.0'),
            ('Server: v0.0.1+g81749d0', '0.0.1'),
            ('Client: v100.100.1000+g928472', '100.100.1000'),
        ]
        for stdout in invalid:
            assert HelmClient(provider=self.dummy_provider)._find_version(stdout) == None

        for stdout, expected in valid:
            assert HelmClient(provider=self.dummy_provider)._find_version(stdout) == expected

    def test_versions_raise_errors(self):
        self.dummy_provider.execute.return_value = HelmCmdResponse(0, '', 'invalid', '')

        for versions in ['client_version', 'server_version']:
            with self.assertRaises(HelmClientException):
                getattr(HelmClient(provider=self.dummy_provider), versions)

    # TODO need to write testing for this filter
    def test_global_argument_filter(self):
        examples = [
            {'original': ['--random', '--debug', '--tiller-namespace asdf'],
             'expected': ['--debug', '--tiller-namespace asdf']},
            {'original': ['--tiller-namespace asdf', '--host somehost.com'],
             'expected': ['--tiller-namespace asdf', '--host somehost.com']},
            {'original': ['--not-valid-host asdf', '--host asdf.com', '--tls-hostname fdsa.com'],
             'expected': ['--host asdf.com']},
            {'original': ['--hosting newval'],
             'expected': []}
        ]

        helm_filter = HelmClient._clean_non_global_flags
        for example in examples:
            helm_filter(example['original'])
            self.assertEqual(example['expected'], example['original'])

    def test_rollback(self):
        with self.assertRaises(NotImplementedError):
            HelmClient(provider=self.dummy_provider).rollback('broken')
