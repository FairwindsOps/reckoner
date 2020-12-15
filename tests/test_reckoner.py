# -- coding: utf-8 --

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


import unittest
from unittest import mock

import coloredlogs
import logging
import os
import shutil
import reckoner
import ruyaml

from reckoner.tests.namespace_manager_mock import NamespaceManagerMock

from reckoner.reckoner import Reckoner
from reckoner.config import Config
from reckoner.course import Course
from reckoner.repository import Repository
from reckoner.helm.client import Helm2Client
from reckoner import exception


class TestBase(unittest.TestCase):

    def setUp(self):
        self.subprocess_mock_patch = mock.patch('subprocess.Popen')
        self.subprocess_mock = self.subprocess_mock_patch.start()
        self.m = mock.Mock()
        Config.reset()

    def configure_subprocess_mock(self, stdout, stderr, returncode):
        attrs = {'returncode': returncode, 'communicate.return_value': (stdout, stderr)}
        self.m.configure_mock(**attrs)
        self.subprocess_mock.return_value = self.m

    def reset_mock(self):
        self.subprocess_mock.reset_mock()

    def tearDown(self):
        self.subprocess_mock_patch.stop()

# Test properties of the mock


@mock.patch('reckoner.reckoner.Config', autospec=True)
@mock.patch('reckoner.reckoner.Course', autospec=True)
@mock.patch.object(Helm2Client, 'tiller_version')
@mock.patch.object(Helm2Client, 'check_helm_command')
class TestReckonerAttributes(TestBase):
    name = "test-reckoner-attributes"

    def setUp(self):
        super(type(self), self).setUp()
        self.configure_subprocess_mock('', '', 0)

    def test_config(self, *args):
        reckoner_instance = reckoner.reckoner.Reckoner()
        self.assertTrue(hasattr(reckoner_instance, 'config'))

    def test_course(self, *args):
        reckoner_instance = reckoner.reckoner.Reckoner()
        self.assertTrue(hasattr(reckoner_instance, 'course'))


@mock.patch('reckoner.chart.NamespaceManager', NamespaceManagerMock)
class TestCourseMocks(unittest.TestCase):

    @mock.patch('reckoner.course.yaml_handler', autospec=True)
    @mock.patch('reckoner.course.get_helm_client', autospec=True)
    def test_raises_errors_when_missing_heading(self, mock_helm, mock_yaml):
        course_yml = {
            'namespace': 'fake',
            'charts': {
                'fake-chart': {
                    'chart': 'none',
                    'version': 'none',
                    'repository': 'none',
                }
            }
        }

        mock_yaml.load.side_effect = [course_yml]
        helm_args = ['provided args']
        helm_instance = mock_helm(helm_args)
        helm_instance.client_version = '0.0.0'

        instance = reckoner.course.Course(None)
        with self.assertRaises(exception.NoChartsToInstall):
            instance.plot(['a-chart-that-is-not-defined'])

    @mock.patch('reckoner.course.yaml_handler', autospec=True)
    @mock.patch('reckoner.course.get_helm_client', autospec=True)
    def test_passes_if_any_charts_exist(self, mock_helm, mock_yaml):
        course_yml = {
            'namespace': 'fake',
            'charts': {
                'fake-chart': {
                    'chart': 'none',
                    'version': 'none',
                    'repository': 'none',
                }
            }
        }

        mock_yaml.load.side_effect = [course_yml]
        # this is not okay I assume, I just added args
        helm_args = ['provided args']
        helm_instance = mock_helm(helm_args)
        helm_instance.client_version = '0.0.0'

        instance = reckoner.course.Course(None)
        self.assertTrue(instance.plot(['a-chart-that-is-not-defined', 'fake-chart']))


test_course = "./tests/test_course.yml"
git_repo_path = "./test"

with open(test_course, 'r') as yaml_stream:
    course_yaml_dict = ruyaml.load(yaml_stream, Loader=ruyaml.Loader)
test_release_names = list(course_yaml_dict['charts'].keys())
test_repositories = ['stable', 'incubator'],
test_minimum_versions = ['helm', 'reckoner']
test_repository_dict = {'name': 'test_repo', 'url': 'https://kubernetes-charts.storage.googleapis.com'}
test_reckoner_version = "1.0.0"
test_namespace = 'test'

test_release_name = 'spotify-docker-gc-again'
test_chart_name = 'spotify-docker-gc'

test_git_repository_chart = 'centrifugo'
test_git_repository = {'path': 'stable', 'git': 'https://github.com/kubernetes/charts.git'}
test_incubator_repository_chart = 'cluster-autoscaler'
test_incubator_repository_str = 'stable'

test_environ_var = 'test_environment_variable_string'
test_environ_var_name = 'test_environ_var'
test_environ_var_chart = "redis"

test_flat_values_chart = 'cluster-autoscaler'
test_flat_values = {
    'string': 'string',
    'integer': 10,
    'boolean': True,
    test_environ_var_name: '${' + str(test_environ_var_name) + '}'
}

test_nested_values_chart = 'centrifugo'
test_nested_values = {
    'even':
        [
            'in',
            'a',
            'list',
            {
                'or':
                    {
                        'dictionary':
                            {
                                'int': 999,
                                'of': 'items',
                                test_environ_var_name: '${' + str(test_environ_var_name) + '}'
                            }
                    }
            }
        ],
    'nested':
        {
            'values':
                {
                    'are': 'supported'
                }
        }
}

test_values_strings_chart = "spotify-docker-gc"

test_default_files_path = "~/.helm"
test_files_path = '../test_files/.helm'
test_archive_pathlet = 'cache/archive'
test_helm_archive = "{}/{}".format(test_files_path, test_archive_pathlet)

test_helm_args = ['helm', 'version', '--client']
test_helm_version_return_string = 'Client: v2.11.0+g2e55dbe'
test_helm_version = '2.11.0'

test_helm_repo_return_string = '''NAME          URL
stable      https://kubernetes-charts.storage.googleapis.com
local       http://127.0.0.1:8879/charts
incubator   https://kubernetes-charts-incubator.storage.googleapis.com'''
test_helm_repo_args = ['helm', 'repo', 'list']
test_helm_repos = [Repository({'url': 'https://kubernetes-charts.storage.googleapis.com', 'name': 'stable'}, mock.Mock()),
                   Repository({'url': 'http://127.0.0.1:8879/charts', 'name': 'local'}, mock.Mock())]

test_tiller_present_return_string = '''NAME         REVISION    UPDATED                     STATUS      CHART
      APP VERSION NAMESPACE centrifugo  1           Tue Oct  2 16:19:01 2018    DEPLOYED    centrifugo-2.0.1    1.7.3
            test '''
test_tiller_present_args = ['helm', 'list']

test_tiller_not_present_return_string = ''
test_tiller_not_present_args = ['helm', 'list']

test_repo_update_return_string = '''Hang tight while we grab the latest from your chart repositories...
...Skip local chart repository
...Successfully got an update from the "incubator" chart repository
...Successfully got an update from the "stable" chart repository
Update Complete. ⎈ Happy Helming!⎈'''
test_repo_update_args = ['helm', 'repo', 'update']

test_repo_install_args = ['helm', 'repo', 'add', 'test_repo', 'https://kubernetes-charts.storage.googleapis.com']
test_repo_install_return_string = '"test_repo" has been added to your repositories'


def setUpModule():
    coloredlogs.install(level="DEBUG")
    Config()

    os.makedirs(test_helm_archive)
    os.environ['HELM_HOME'] = test_files_path

    # This will eventually be need for integration testing
    # args = ['helm','init','-c','--home', "{}/.helm".format(test_files_path)]
    # subprocess.check_output(args)


def tearDownModule():
    shutil.rmtree(test_files_path)


@mock.patch('reckoner.chart.NamespaceManager', NamespaceManagerMock)
class TestReckoner(TestBase):
    name = "test-pentagon-base"

    @mock.patch('reckoner.course.get_helm_client', autospec=True)
    def setUp(self, mock_helm_client_course_scope):
        mock_helm_client_course_instance = mock_helm_client_course_scope([])
        mock_helm_client_course_instance.version = "100.100.100"
        super(type(self), self).setUp()
        self.configure_subprocess_mock(test_tiller_present_return_string, '', 0)
        with open(test_course) as f:
            self.a = Reckoner(course_file=f)

    def test_instance(self):
        self.assertIsInstance(self.a, Reckoner)

    def test_config_instance(self):
        self.assertIsInstance(self.a.config, Config)

    @mock.patch('reckoner.repository.git', autospec=True)
    def test_install(self, mock_git_lib):
        self.assertEqual(self.a.install(), None)


@mock.patch('reckoner.chart.NamespaceManager', NamespaceManagerMock)
class TestCourse(TestBase):

    @mock.patch('reckoner.course.get_helm_client', autospec=True)
    def setUp(self, mock_helm_client_course_scope, autospec=True):
        mock_helm_client_course_instance = mock_helm_client_course_scope([])
        mock_helm_client_course_instance.version = '100.100.100'
        super(type(self), self).setUp()
        self.configure_subprocess_mock(test_repo_update_return_string, '', 0)
        with open(test_course) as f:
            self.c = Course(f)

        self.test_repository = Repository(test_repository_dict, None)

    def test_config_instance(self):
        self.assertIsInstance(self.c.config, Config)

    def test_course_values(self):
        self.assertIsInstance(self.c, Course)
        self.assertEqual([chart._release_name for chart in self.c.charts], test_release_names)
        self.assertNotEqual([chart.name for chart in self.c.charts], test_release_names,
                            msg="All the release names match the chart names, this may happen if you've edited the "
                                "test_course.yml and not provided an example with a different chart_name and chart.")
        self.assertEqual(self.c.repositories[0].name, test_repository_dict['name'])
        self.assertEqual(self.c.repositories[0].url, test_repository_dict['url'])
        self.assertEqual(list(self.c.minimum_versions.keys()), test_minimum_versions)
        self.assertIsInstance(self.c.repositories, list)

    def test_plot_course(self):
        self.configure_subprocess_mock('', '', 0)  # TODO: Lots of work do do here on installation of the list of charts
        self.c.plot(list(self.c._dict['charts']))
        self.assertEqual(self.c._only_charts, self.c.charts)


@mock.patch('reckoner.chart.NamespaceManager', NamespaceManagerMock)
class TestChart(TestBase):

    @mock.patch('reckoner.course.get_helm_client', autospec=True)
    def setUp(self, mock_helm_client_course_scope):
        mock_helm_client_course_instance = mock_helm_client_course_scope([])
        mock_helm_client_course_instance.version = "100.100.100"
        self.helm_client_mock = mock_helm_client_course_instance
        super(type(self), self).setUp()
        self.configure_subprocess_mock(test_tiller_present_return_string, '', 0)
        with open(test_course) as f:
            self.a = Reckoner(course_file=f)
        self.charts = self.a.course.charts

    def test_releasename_is_different_than_chart_name(self):
        for chart in self.charts:
            if chart == test_release_name:
                self.assertNotEqual(chart._release_name, chart.name)
                self.assertEqual(chart.name, test_chart_name)

    def test_chart_repositories(self):
        for chart in self.charts:
            self.assertIsNotNone(chart.repository)
            self.assertIsInstance(chart.repository, Repository)
            if chart.name == test_git_repository_chart:
                self.assertEqual(chart.repository.git, Repository(test_git_repository, mock.Mock()).git)
                self.assertEqual(chart.repository.path, Repository(test_git_repository, mock.Mock()).path)
            elif chart.name == test_incubator_repository_chart:
                self.assertEqual(chart.repository.name, Repository(test_incubator_repository_str, mock.Mock()).name)
                self.assertIsNone(chart.repository.url)

    def test_chart_set_values(self):
        for chart in self.charts:
            if chart.name == test_flat_values_chart:
                self.assertEqual(chart.set_values, test_flat_values)
                self.assertIsInstance(chart.set_values, dict)
                self.assertIsInstance(chart.set_values['string'], str)
                self.assertIsInstance(chart.set_values['integer'], int)
                self.assertIsInstance(chart.set_values['boolean'], bool)
            elif chart.name == test_nested_values_chart:
                self.assertEqual(chart.set_values, test_nested_values)
            elif chart.release_name == test_values_strings_chart:
                self.assertIsInstance(chart.values_strings['string'], str)
                self.assertIsInstance(chart.values_strings['integer'], int)
                self.assertIsInstance(chart.values_strings['boolean'], bool)

    # FIXME: Related to the FIXME in install() of Chart class.
    @unittest.skip("Skipping non-implemented test.")
    def test_chart_at_git_root(self):
        """
        Chart should support cloning git repositories where the chart is in
        the root of the repository.
        """
        pass

    @mock.patch('reckoner.repository.git', autospec=True)
    def test_chart_install(self, mock_git_lib):
        for chart in self.charts:
            os.environ[test_environ_var_name] = test_environ_var
            assert chart.install(test_namespace) is None
            self.helm_client_mock.upgrade.assert_called()
            logging.debug(chart)

            # TODO - we really need to refactor this to be better about testing in the same layer
            #        this is traversing many layers in the code that could be better encapsulated

            last_mock = self.helm_client_mock.upgrade.call_args_list[-1][0][0]

            if chart.name == test_environ_var_chart:
                logging.error(last_mock)
                self.assertEqual(
                    last_mock,
                    [
                        chart.release_name,
                        chart.repository.chart_path,
                        '--namespace',
                        '{}'.format(chart.namespace),
                        '--set',
                        '{}={}'.format(test_environ_var_name, test_environ_var)]
                )
            if chart.release_name == test_values_strings_chart:
                self.assertEqual(
                    last_mock,
                    [
                        chart.release_name,
                        chart.repository.chart_path,
                        '--namespace',
                        '{}'.format(chart.namespace),
                        '--version',
                        '0.1.0',
                        '--set-string',
                        'string=string',
                        '--set-string',
                        'integer=10',
                        '--set-string',
                        'boolean=True'
                    ]
                )


class TestRepository(TestBase):

    @mock.patch('reckoner.repository.git', autospec=True)
    def test_git_repository(self, mock_git_lib):
        helm_mock = mock.Mock()
        helm_mock.repositories = []
        r = Repository(test_git_repository, helm_mock)
        self.assertIsInstance(r, Repository)
        self.assertEqual(r.git, test_git_repository['git'])
        self.assertEqual(r.path, test_git_repository['path'])
        self.assertEqual(r.install("test_chart"), None)

    def test_tgz_repository(self):
        helm_mock = mock.Mock()
        helm_mock.repositories = []
        r = Repository(test_repository_dict, helm_mock)
        self.assertIsInstance(r, Repository)
        self.assertEqual(r.name, test_repository_dict['name'])
        self.assertEqual(r.url, test_repository_dict['url'])
        assert r.install("test_chart")


class TestConfig(TestBase):

    def setUp(self):
        super(type(self), self).setUp()
        self.c1 = Config()
        self.c2 = Config()

    def test_borg_pattern(self):
        self.assertEqual(self.c1.__dict__, self.c2.__dict__)
        self.c1.test = 'value'
        self.assertEqual(self.c1.__dict__, self.c2.__dict__)
        self.assertIs(self.c1.test, self.c2.test)
        self.assertIsNot(self.c1, self.c2)
