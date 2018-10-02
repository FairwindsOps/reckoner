
import unittest

import coloredlogs
import logging
import os
import git
import subprocess
import shutil

from autohelm.autohelm import AutoHelm
from autohelm.config import Config
from autohelm.course import Course
from autohelm.repository import Repository
from autohelm.exception import MinimumVersionException

test_course = "./tests/test_course.yml"
git_repo_path = "./test"

test_release_names = ['cluster-autoscaler', 'spotify-docker-gc', 'centrifugo', 'spotify-docker-gc-again']
test_repositories = ['stable', 'incubator'],
test_minimum_versions = ['helm', 'autohelm']
test_repository_dict = {'name': 'test_repo', 'url': 'https://test_repo_url'}
test_autohelm_version = "1.0.0"

test_release_name = 'spotify-docker-gc-again'
test_chart_name = 'spotify-docker-gc'

test_git_repository_chart = 'centrifugo'
test_git_repository = {'path': 'stable', 'git': 'https://github.com/kubernetes/charts.git'}
test_incubator_repository_chart = 'cluster-autoscaler'
test_incubator_repository_str = 'incubator'

test_flat_values_chart = 'cluster-autoscaler'
test_flat_values = {
    'string': 'string',
    'integer': 10,
    'boolean': True,
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
                    'of':
                    'items'
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

test_files_path = "test_files/.helm"
test_helm_archive = "{}/cache/archive/".format(test_files_path)


def setUpModule():
    coloredlogs.install(level="DEBUG")
    config = Config()
    config.local_development = True

    os.makedirs(test_helm_archive)
    os.environ['HELM_HOME'] = test_files_path

    # This will eventually be need for integration testing
    # args = ['helm','init','-c','--home', "{}/.helm".format(test_files_path)]
    # subprocess.check_output(args)


def tearDownModule():
    pass #shutil.rmtree(test_files_path)


class TestAutoHelm(unittest.TestCase):
    name = "test-pentagon-base"

    def setUp(self):

        # This will eventually be need for integration testing
        # repo = git.Repo.init(git_repo_path)
        # os.chdir(git_repo_path)
        # subprocess.call(["helm", "create", "chart"])
        # # Create git chart in a git repo, then have it checkout the repo from that location
        # logging.debug(os.listdir("./"))
        # os.chdir("../")
        with open(test_course) as f:
            self.a = AutoHelm(file=f, local_development=True)

    # def tearDown(self):
    #     self.a = None
    #     subprocess.call(['rm', '-rf', git_repo_path])

    def test_instance(self):
        self.assertIsInstance(self.a, AutoHelm)

    def test_config_instance(self):
        self.assertIsInstance(self.a.config, Config)

    def test_install(self):
        print self.a.course.repositories

        self.assertTrue(self.a.install())


class TestCourse(unittest.TestCase):

    def setUp(self):

        with open(test_course) as f:
            self.c = Course(f)

        self.test_repository = Repository(test_repository_dict)

    def test_config_instance(self):
        self.assertIsInstance(self.c.config, Config)

    def test_course_values(self):
        self.assertIsInstance(self.c, Course)
        self.assertEqual([chart._release_name for chart in self.c.charts], test_release_names)
        self.assertNotEqual([chart.name for chart in self.c.charts], test_release_names)
        self.assertEqual(self.c.repositories[0].name, test_repository_dict['name'])
        self.assertEqual(self.c.repositories[0].url,  test_repository_dict['url'])
        self.assertEqual(self.c.minimum_versions.keys(), test_minimum_versions)
        self.assertIsInstance(self.c.repositories, list)

    def test_minimum_version(self):
        self.c.minimum_versions['autohelm'] = test_autohelm_version
        self.assertRaises(MinimumVersionException, self.c._compare_required_versions)

    def test_plot_course(self):
        self.c.plot(list(self.c._dict['charts']))
        self.assertEqual(self.c._charts_to_install, self.c.charts)


class TestChart(unittest.TestCase):

    def setUp(self):
        with open(test_course) as f:
            self.a = AutoHelm(file=f, local_development=True)
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
                self.assertEqual(chart.repository.git, Repository(test_git_repository).git)
                self.assertEqual(chart.repository.path, Repository(test_git_repository).path)
            elif chart.name == test_incubator_repository_chart:
                self.assertEqual(chart.repository.name, Repository(test_incubator_repository_str).name)
                self.assertIsNone(chart.repository.url)

    def test_chart_values(self):
        for chart in self.charts:
            if chart.name == test_flat_values_chart:
                self.assertEqual(chart.values, test_flat_values)
                self.assertIsInstance(chart.values, dict)
                self.assertIsInstance(chart.values['string'], str)
                self.assertIsInstance(chart.values['integer'], int)
                self.assertIsInstance(chart.values['boolean'], bool)
            elif chart.name == test_nested_values_chart:
                self.assertEqual(chart.values, test_nested_values)
            elif chart.release_name == test_values_strings_chart:
                self.assertEqual(chart.values_strings, test_flat_values,)
                self.assertIsInstance(chart.values_strings['string'], str)
                self.assertIsInstance(chart.values_strings['integer'], int)
                self.assertIsInstance(chart.values_strings['boolean'], bool)

    def test_debug_args(self):
        chart = self.charts[0]

        chart.config.debug = True
        self.assertEqual(chart.debug_args, ['--debug'])

        chart.config.debug = False
        chart.config.dryrun = True
        self.assertEqual(chart.debug_args, ['--dry-run', '--debug'])


class TestRepository(unittest.TestCase):

    def test_git_repository(self):
        r = Repository(test_git_repository)
        self.assertIsInstance(r, Repository)
        self.assertEqual(r.git, test_git_repository['git'])
        self.assertEqual(r.path, test_git_repository['path'])
        self.assertEqual(r.install(), True)
        self.assertEqual(r.update(), True)

    def test_tgz_repository(self):
        r = Repository(test_repository_dict)
        self.assertIsInstance(r, Repository)
        self.assertEqual(r.name, test_repository_dict['name'])
        self.assertEqual(r.url, test_repository_dict['url'])
        self.assertEqual(r.install(), True)
        self.assertEqual(r.update(), True)


class TestConfig(unittest.TestCase):

    def setUp(self):
        self.c1 = Config()
        self.c2 = Config()

    def test_equal(self):
        self.assertEqual(self.c1.__dict__, self.c2.__dict__)
        self.c1.test = 'value'
        self.assertEqual(self.c1.__dict__, self.c2.__dict__)
