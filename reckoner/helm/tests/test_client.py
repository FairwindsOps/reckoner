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

from reckoner.helm.client import HelmClient, Helm3Client, HelmClientException, HelmVersionException, get_helm_client
from reckoner.helm.command import HelmCommand
from reckoner.helm.cmd_response import HelmCmdResponse
from reckoner.helm.provider import HelmProvider
import unittest
from unittest import mock


class TestHelm3Client(unittest.TestCase):
    def setUp(self):
        self.dummy_provider = mock.Mock()

    def test_default_helm_arguments(self):
        helm_client = Helm3Client(provider=self.dummy_provider)
        assert hasattr(helm_client, 'default_helm_arguments')

    def test_version(self):
        self.dummy_provider.execute.return_value = HelmCmdResponse(0, '', 'v0.0.0+gabcdef01234', '')
        assert '0.0.0' == Helm3Client(provider=self.dummy_provider).version

    def test_public_methods(self):
        helm_client = Helm3Client(provider=self.dummy_provider)
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

        assert Helm3Client(provider=self.dummy_provider).repositories == repositories_expected

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

        assert Helm3Client(provider=self.dummy_provider).repositories == repositories_expected

    def test_execute_with_additional_parameters(self):
        default_params = ['--some params']
        adhoc_params = ['--some more']
        expected_params = default_params + adhoc_params

        Helm3Client(
            default_helm_arguments=default_params,
            provider=self.dummy_provider
        ).execute('version', adhoc_params)

        assert self.dummy_provider.execute.call_args[0][0].arguments == expected_params

    def test_execute_with_default_helm_arguments(self):
        expected_params = ['--some params', '--found']
        helm_client = Helm3Client(provider=self.dummy_provider)
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
        assert Helm3Client(provider=self.dummy_provider).check_helm_command() == True
        with self.assertRaises(HelmClientException) as e:
            assert Helm3Client(provider=self.dummy_provider).check_helm_command() == False

    def test_default_upgrade_calls_install_flag(self):
        Helm3Client(provider=self.dummy_provider).upgrade([])
        self.dummy_provider.execute.called_once()
        self.assertEqual(self.dummy_provider.execute.call_args[0][0].command, "upgrade")
        self.assertEqual(self.dummy_provider.execute.call_args[0][0].arguments, ["--install"])
        self.dummy_provider.reset_mock()

    def test_upgrade(self):
        Helm3Client(provider=self.dummy_provider).upgrade([], install=True)
        self.dummy_provider.execute.called_once()
        self.assertEqual(self.dummy_provider.execute.call_args[0][0].command, "upgrade")
        self.assertEqual(self.dummy_provider.execute.call_args[0][0].arguments, ["--install"])
        self.dummy_provider.reset_mock()

        Helm3Client(provider=self.dummy_provider).upgrade([], install=False)
        self.dummy_provider.execute.called_once()
        self.assertEqual(self.dummy_provider.execute.call_args[0][0].command, "upgrade")
        self.assertEqual(self.dummy_provider.execute.call_args[0][0].arguments, [])
        self.dummy_provider.reset_mock()

    def test_upgrade_with_plugin(self):
        plugin_name = 'some-plugin'

        Helm3Client(provider=self.dummy_provider).upgrade([], install=True, plugin=plugin_name)
        self.dummy_provider.execute.assert_called_once()

        self.assertEqual(self.dummy_provider.execute.call_args[0][0].command, plugin_name)
        self.assertEqual(self.dummy_provider.execute.call_args[0][0].arguments, ["upgrade", "--install"])

        self.dummy_provider.reset_mock()

        Helm3Client(provider=self.dummy_provider).upgrade([], install=False, plugin=plugin_name)
        self.dummy_provider.execute.assert_called_once()

        self.assertEqual(self.dummy_provider.execute.call_args[0][0].command, plugin_name)
        self.assertEqual(self.dummy_provider.execute.call_args[0][0].arguments, ["upgrade"])

    def test_dependency_update(self):
        Helm3Client(provider=self.dummy_provider).dependency_update('chart_path')
        self.dummy_provider.execute.assert_called_once

    def test_repo_update(self):
        Helm3Client(provider=self.dummy_provider).repo_update()
        self.dummy_provider.execute.assert_called_once

    def test_verify_default_helm_args_intantiate(self):
        # Should support instantiate with None
        assert Helm3Client(provider=self.dummy_provider, default_helm_arguments=None)

        # Should raise errors on all other non iterators
        for invalid in [str('invalid'), 1, 0.01, True]:
            with self.assertRaises(ValueError):
                Helm3Client(default_helm_arguments=invalid)

    def test_repo_add(self):
        Helm3Client(provider=self.dummy_provider).repo_add('new', 'url')
        self.dummy_provider.execute.assert_called_once

    def test_version_regex(self):
        invalid = [
            'not valid',
        ]

        valid = [
            ('v3.0+unreleased+g30525d7', '3.0'),
            ('v3.0.0-alpha.2+g97e7461', '3.0.0'),
            ('v3.0.0-beta.3+g5cb923e', '3.0.0')
        ]
        for stdout in invalid:
            assert Helm3Client(provider=self.dummy_provider)._find_version(stdout) == None

        for stdout, expected in valid:
            assert Helm3Client(provider=self.dummy_provider)._find_version(stdout) == expected

    def test_versions_raise_errors(self):
        self.dummy_provider.execute.return_value = HelmCmdResponse(0, '', 'invalid', '')

        for versions in ['version']:
            with self.assertRaises(HelmClientException):
                getattr(Helm3Client(provider=self.dummy_provider), versions)

    # TODO need to write testing for this filter
    def test_global_argument_filter(self):
        examples = [
            {'original': ['--random', '--debug'],
             'expected': ['--debug']},
            {'original': ['--hosting newval'],
             'expected': []}
        ]

        helm_filter = Helm3Client._clean_non_global_flags
        for example in examples:
            helm_filter(example['original'])
            self.assertEqual(example['expected'], example['original'])

    def test_rollback(self):
        with self.assertRaises(NotImplementedError):
            Helm3Client(provider=self.dummy_provider).rollback('broken')

    def test_get_version(self):
        with self.assertRaises(HelmClientException):
            provider_mock = mock.Mock(autospec=HelmProvider)
            provider_mock.execute.side_effect = [
                HelmCmdResponse(1, '', '', None),
            ]
            client = Helm3Client(provider=provider_mock)
            client._get_version()

    def test_get_cache(self):
        env_response = """
HELM_BIN="/Users/test/.asdf/installs/helm/3.2.4/bin/helm"
HELM_DEBUG="false"
HELM_KUBEAPISERVER=""
HELM_KUBECONTEXT=""
HELM_KUBETOKEN=""
HELM_NAMESPACE="default"
HELM_PLUGINS="/Users/testLibrary/helm/plugins"
HELM_REGISTRY_CONFIG="/Users/test/Library/Preferences/helm/registry.json"
HELM_REPOSITORY_CACHE="/Users/test/Library/Caches/helm/repository"
HELM_REPOSITORY_CONFIG="/Users/test/Library/Preferences/helm/repositories.yaml
"""
        self.dummy_provider.execute.return_value = HelmCmdResponse(0, '', env_response, '')
        assert "/Users/test/Library/Caches/helm/repository" == Helm3Client(provider=self.dummy_provider).cache


class TestGetHelmClient(unittest.TestCase):
    """Testing the get_helm_client factory to get different versions of helm based on results from helm calls"""

    def test_get_helm_3_client(self):
        """Test getting a helm 3 client when passed certian info"""
        provider_mock = mock.MagicMock(HelmProvider, autospec=True)
        provider_mock.execute.side_effect = mock_execute_helm3provider
        helm_client = get_helm_client([], helm_provider=provider_mock)
        self.assertIsInstance(helm_client, Helm3Client)

    def test_static_version_selection(self):
        """Test that when we explicitly want helm3 we get that "client" class"""
        provider_mock = mock.MagicMock(HelmProvider, autospec=True)
        provider_mock.execute.side_effect = mock_execute_helm3provider
        helm_client = get_helm_client([], client_version="3", helm_provider=provider_mock)
        self.assertIsInstance(helm_client, Helm3Client)

    def test_handling_err_get_client(self):
        """Test error handling for helm output"""
        provider_mock = mock.MagicMock(HelmProvider, autospec=True)
        provider_mock.execute.side_effect = mock_execute_unknown_helm_provider
        # Tests if we pass a non-conforming version string with a healthy exit code based on helm 3 not supporting --client
        with self.assertRaises(HelmClientException):
            get_helm_client([], helm_provider=provider_mock)

        provider_mock.execute.side_effect = Exception('totally unexpected exception')
        with self.assertRaises(HelmClientException):
            get_helm_client([], helm_provider=provider_mock)

    def test_non_existent_versions(self):
        """Test that we only accept 3 for helm version"""
        with self.assertRaises(HelmClientException):
            provider_mock = mock.MagicMock(HelmProvider, autospec=True)
            provider_mock.execute.side_effect = []
            get_helm_client([], client_version="1001", helm_provider=provider_mock)


def mock_execute_helm3provider(helm_command):
    if helm_command.command == 'version':
        if '--client' in helm_command.arguments:
            return HelmCmdResponse(
                exit_code=1,
                stderr='helm 3 does not accept the --client flag',
                stdout='',
                command=helm_command,
            )
        return HelmCmdResponse(
            exit_code=0,
            stderr='',
            stdout='v3.0.0-beta.3+g5cb923e',
            command=helm_command,
        )


def mock_execute_unknown_helm_provider(helm_command):
    if helm_command.command == 'version':
        if '--client' in helm_command.arguments:
            return HelmCmdResponse(
                exit_code=1,
                stderr='i am a helm 3 client and i break on --client',
                stdout='',
                command=helm_command,
            )
        return HelmCmdResponse(
            exit_code=0,
            stderr='',
            stdout='not a valid version',
            command=helm_command,
        )
