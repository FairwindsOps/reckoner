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
import os
import unittest
from unittest import mock
from reckoner.hooks import Hook
from reckoner.course import Course
from reckoner.secrets import Secret
from reckoner.command_line_caller import Response
from reckoner.helm.client import HelmClientException
from reckoner.exception import ReckonerException, ReckonerCommandException

from .namespace_manager_mock import NamespaceManagerMock


@mock.patch('reckoner.repository.Repository', autospec=True)
@mock.patch('reckoner.course.sys')
@mock.patch('reckoner.course.yaml_handler', autospec=True)
@mock.patch('reckoner.course.get_helm_client', autospec=True)
@mock.patch('reckoner.course.Config', autospec=True)
class TestMinVersion(unittest.TestCase):

    def test_init_error_fails_min_version_reckoner(self, configMock, helmClientMock, yamlLoadMock, sysMock, repoMock):
        """Tests that minimum version will throw an exit."""
        c = configMock()
        c.helm_args = ['provided args']

        yamlLoadMock.load.return_value = {
            'repositories': {
                'name': {},
            },
            'helm_args': None,
            'minimum_versions': {
                'reckoner': '1000.1000.1000',  # minimum version needed
                # find the version of reckoner at meta.py __version__
            }
        }

        sysMock.exit.return_value = None

        Course(None)

        sysMock.exit.assert_called_once
        return True

    def test_init_error_fails_min_version_helm(self, configMock, helmClientMock, yamlLoadMock, sysMock, repoMock):
        """Tests that minimum version will throw an exit."""
        c = configMock()
        c.helm_args = ['provided args']

        h = helmClientMock(c.helm_args)
        h.version = '0.0.1'

        yamlLoadMock.load.return_value = {
            'repositories': {
                'name': {},
            },
            'helm_args': None,
            'minimum_versions': {
                'helm': '1000.1000.1000',  # minimum version needed
            }
        }

        sysMock.exit.return_value = None

        Course(None)

        sysMock.exit.assert_called_once
        return True


class TestIntegrationWithChart(unittest.TestCase):

    @mock.patch('reckoner.chart.NamespaceManager', NamespaceManagerMock)
    @mock.patch('reckoner.chart.Config', autospec=True)
    @mock.patch('reckoner.hooks.call', autospec=True)
    @mock.patch('reckoner.repository.Repository', autospec=True)
    @mock.patch('reckoner.course.sys')
    @mock.patch('reckoner.course.yaml_handler', autospec=True)
    @mock.patch('reckoner.course.get_helm_client', autospec=True)
    @mock.patch('reckoner.course.Config', autospec=True)
    def test_failed_pre_install_hooks_fail_chart_installation(self, configMock, helmClientMock, yamlLoadMock, sysMock, repoMock, hookCallMock, chartConfigMock):
        """Test that the chart isn't installed when the pre_install hooks return any non-zero responses. This also assures we don't raise python errors with hook errors."""
        c = configMock()
        c.continue_on_error = False
        c.helm_args = ['provided args']
        chartConfig = chartConfigMock()
        chartConfig.course_base_directory = '.'
        chartConfig.dryrun = False
        chartConfig.create_namespace = True
        chartConfig.cluster_namespaces = []

        h = helmClientMock(c.helm_args)
        h.client_version = '0.0.1'

        yamlLoadMock.load.return_value = {
            'charts': {
                'first-chart': {
                    'hooks': {
                        'pre_install': [
                            'run a failed command here',
                        ]
                    }
                }
            }
        }

        course = Course(None)
        with self.assertRaises(ReckonerCommandException):
            results = course.plot(['first-chart'])


@mock.patch('reckoner.course.yaml_handler', autospec=True)
@mock.patch('reckoner.course.get_helm_client', autospec=True)
@mock.patch('reckoner.course.Hook.run', autospec=True)
class TestCourse(unittest.TestCase):

    def setUp(self):
        self.course_yaml = {
            'charts': {
                'first-chart': {
                    'repository': 'stable',
                    'chart': 'nonexistant',
                    'version': '0.0.0',
                }
            },
            'hooks':
            {
                "pre_install": ['command1', 'command2'],
                "post_install": ['command3', 'command4'],
            }
        }

    def test_hooks_parsed(self, mockHook, mockGetHelm, mockYAML):
        mockYAML.load.return_value = self.course_yaml
        course = Course(None)

        self.assertIsInstance(course.hooks, (dict))
        self.assertIsInstance(course.pre_install_hook, (Hook))
        self.assertIsInstance(course.post_install_hook, (Hook))

        self.assertEqual(course.pre_install_hook.commands, ['command1', 'command2'])
        self.assertEqual(course.post_install_hook.commands, ['command3', 'command4'])

    def test_secrets_parsed(self, mockHook, mockGetHelm, mockYAML):

        course_with_secrets = self.course_yaml.copy()
        # Doing this because the way secrets get injected into the environment
        # there was a naming collision every subsequent time this loaded
        course_with_secrets['secrets'] = [
            {
                'name': 'TEST_SECRET',
                'backend': 'ShellExecutor',
                'script': 'echo foo'
            }
        ]

        mockYAML.load.return_value = course_with_secrets
        course = Course(None)

        self.assertIsInstance(course.secrets, (list))
        self.assertIsInstance(course.secrets[0], (Secret))

    def test_secret_error_with_set_environment(self, mockHook, mockGetHelm, mockYAML):

        course_with_secrets = self.course_yaml.copy()
        course_with_secrets['secrets'] = [
            {
                'name': 'TEST_SECRET',
                'backend': 'ShellExecutor',
                'script': 'false'
            }
        ]

        mockYAML.load.return_value = course_with_secrets
        os.environ['TEST_SECRET'] = "SET"
        with self.assertRaises(ReckonerException):
            course = Course(None)
            course.merge_secrets_into_environment()

    def test_secret_error_with_get_value(self, mockHook, mockGetHelm, mockYAML):

        course_with_secrets = self.course_yaml.copy()
        course_with_secrets['secrets'] = [
            {
                'name': 'TEST_SECRET',
                'backend': 'ShellExecutor',
                'script': 'false'
            }
        ]

        mockYAML.load.return_value = course_with_secrets
        with self.assertRaises(ReckonerCommandException):
            course = Course(None)
            course.merge_secrets_into_environment()

    def test_plot(self, mockHook, mockGetHelm, mockYAML):
        mockYAML.load.return_value = self.course_yaml
        course = Course(None)
        assert course.plot(['first-chart'])

    def test_str_output(self, mockHook, mockGetHelm, mockYAML):
        mockYAML.load.return_value = self.course_yaml
        assert Course(None).__str__()

    def test_chart_install_logic(self, mockHook, mockGetHelm, mockYAML):
        mockYAML.load.return_value = {
            'charts': {
                'first-chart': {},
                'second-chart': {}
            }
        }

        # expect the first chart install to bubble up an error
        chart = mock.MagicMock()
        chart.result = None
        chart.install.side_effect = Exception("Second command has an error")

        course = Course(None)
        with self.assertRaises(ReckonerCommandException):
            course.install_charts([chart, chart])

        # Does not raise because continue or error is True
        course.config.continue_on_error = True
        self.assertEqual(len(course.install_charts([chart, chart])), 2)

    def test_course_raises_errors_on_bad_client_response(self, mockHook, mockGetHelm, mockYAML, *args):
        """Make sure course wraps get_helm_client exceptions as ReckonerExceptions"""
        # Load the course "yaml"
        mockYAML.load.return_value = self.course_yaml

        # Check helm client exception checking command
        mockGetHelm.side_effect = HelmClientException('broken')
        with self.assertRaises(ReckonerException):
            Course(None)
        mockGetHelm.assert_called_once()
        mockGetHelm.reset_mock()

        mockGetHelm.side_effect = Exception("it's a mock: had an error starting helm client")
        with self.assertRaises(ReckonerException):
            Course(None)

    # This test is intended to test the implementation that repository field in charts is resolved to the repositories settings in course.yml; because the repositories code is brittle.
    # This is important because if the chart references a git repo from the main course repositories, it breaks the repo install method
    def test_course_git_repository_handling(self, mockHook, mockGetHelm, mockYAML):
        """Assure that course replaces strings with object settings for chart repository settings"""
        course = mockYAML.load.return_value = self.course_yaml
        # Add repositories configuration to the course
        course['repositories'] = {
            'some-git-repo': {
                'git': 'https://git.com/my-chart.git',
                'path': 'charts',
            },
            'stablez': {
                'url': 'https://fake.url.com',
            }
        }
        # Add first chart reference to the repositories settings
        course['charts']['first-chart']['repository'] = 'some-git-repo'
        # Add second chart referencing a missing chart (current behavior is to keep the string)
        course['charts']['second-chart'] = {
            'repository': 'missingfromrepos',
            'chart': 'my-chart',
        }
        # Add a third chart referring to a non-git repo
        course['charts']['third-chart'] = {
            'chart': 'my-chart',
            'repository': 'stablez',
        }

        self.assertIsInstance(course['charts']['first-chart']['repository'], str)

        # Mock out the repository helm client
        with mock.patch('reckoner.repository.HelmClient', mockGetHelm):
            # Run the course to convert the chart['first-chart']['repository'] reference
            Course(None)

        # Assert the chart repo setting went from string to dict
        self.assertIsInstance(course['charts']['first-chart']['repository'], dict)

        # Assert that the dict for the repositories settings is the same as the charts repository setting after course loads
        self.assertDictEqual(course['charts']['first-chart']['repository'], course['repositories']['some-git-repo'])

        # Assert that second-chart is left alone since it is not in repositories
        self.assertEqual(course['charts']['second-chart']['repository'], 'missingfromrepos')

        # Assert that third-chart is reconciled to settings from repositories block
        self.assertDictEqual(course['charts']['third-chart']['repository'], course['repositories']['stablez'])

# TODO: Add test for calling plot against a chart that doesn't exist in your course.yml

    def test_course_namespace_and_without_namespace_management_handling(self, mockHook, mockGetHelm, mockYAML):
        """Assure that course replaces strings with object settings for chart repository settings"""
        course = mockYAML.load.return_value = self.course_yaml
        course['namespace'] = "test-namespace"

        # Mock out the repository helm client
        with mock.patch('reckoner.repository.HelmClient', mockGetHelm):
            # Run the course to convert the chart['first-chart']['repository'] reference
            c = Course(None)

        # Assert the chart namespace is string
        self.assertIsInstance(course['namespace'], str)

        # Assert that the dict for the namespace manager is the same after course loads
        # expect the first chart install to bubble up an error
        chart = mock.MagicMock()
        c.install_charts([chart])
        chart.install.assert_called_with(
            context=c.context,
            default_namespace=c.namespace,
            default_namespace_management=c.namespace_management
        )

    def test_course_namespace_and_management_handling(self, mockHook, mockGetHelm, mockYAML):
        """Assure that course replaces strings with object settings for chart repository settings"""
        course = mockYAML.load.return_value = self.course_yaml
        course['namespace'] = "test-namespace"
        course['namespace_management'] = {
            "default": {
                "metadata": {
                    "annotations": {
                        "a-one": "a1",
                        "a-two": "a2"
                    },
                    "labels": {
                        "l-one": "l1",
                        "l-two": "l2",
                    }
                },
                "settings": {
                    "overwrite": True
                }
            }
        }

        # Mock out the repository helm client
        with mock.patch('reckoner.repository.HelmClient', mockGetHelm):
            # Run the course to convert the chart['first-chart']['repository'] reference
            c = Course(None)

        # Assert the chart namespace is string
        self.assertIsInstance(course['namespace'], str)

        # Assert that the dict for the namespace manager is the same after course loads
        self.assertDictEqual(
            c.namespace_management,
            {
                "metadata": {
                    "annotations": {
                        "a-one": "a1",
                        "a-two": "a2"
                    },
                    "labels": {
                        "l-one": "l1",
                        "l-two": "l2",
                    }
                },
                "settings": {
                    "overwrite": True
                }
            }
        )
        # expect the first chart install to bubble up an error
        chart = mock.MagicMock()
        c.install_charts([chart])
        chart.install.assert_called_with(
            context=c.context,
            default_namespace=c.namespace,
            default_namespace_management=c.namespace_management
        )
