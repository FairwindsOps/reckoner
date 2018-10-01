
import unittest

import coloredlogs
import logging
import os
import git
import subprocess

from autohelm import AutoHelm
from autohelm.config import Config
from autohelm.course import Course
from autohelm.repository import Repository
from autohelm.exception import MinimumVersionException

test_course = "./tests/test_course.yml"
git_repo_path = "./test"

test_chart_names = ['cluster-autoscaler', 'spotify-docker-gc', 'centrifugo']
test_repositories = ['stable', 'incubator'],
test_minimum_versions = ['helm', 'autohelm']
test_repository_dict = {'name': 'test_repo', 'url': 'test_repo_url'}
test_autohelm_version = "1.0.0"


class TestAutohelm(unittest.TestCase):
    name = "test-pentagon-base"

    def setUp(self):
        coloredlogs.install(level="DEBUG")
        #self.config.home = "./"

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


class TestCourse(unittest.TestCase):

    def setUp(self):
        coloredlogs.install(level="DEBUG")
        self.config = Config()
        self.config.local_development = True

        with open(test_course) as f:
            self.c = Course(f)

        self.test_repository = Repository(test_repository_dict)

    def test_course_values(self):
        self.assertIsInstance(self.c, Course)
        self.assertEqual(self.c.charts.keys(), test_chart_names)
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
