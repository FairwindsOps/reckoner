# -- coding: utf-8 --

# Copyright 2017 Reactive Ops Inc.
#
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import semver
import traceback
import reckoner

import oyaml as yaml

from config import Config
from chart import Chart
from repository import Repository
from exception import MinimumVersionException, ReckonerCommandException
from helm import Helm

from meta import __version__ as reckoner_version


class Course(object):
    """
    Description:
    - Top level class for the attribues of the course.yml file
    - Parses yaml file into verious Reckoner classes

    Arguments:
    - file (File)

    Attributes:
    - config: Instance of Config()
    - helm: Instance of Helm()
    - charts: List of Chart() instances
    - repositories: List of Repository() instances

    """

    def __init__(self, file):
        """
        Parse course.yml contents into instances.
        """
        self.config = Config()
        self.helm = Helm()
        self._dict = yaml.load(file)
        self._repositories = []
        self._charts = []
        for name, repository in self._dict.get('repositories', {}).iteritems():
            repository['name'] = name
            self._repositories.append(Repository(repository))

        for name, chart in self._dict.get('charts', {}).iteritems():
            self._charts.append(Chart({name: chart}))

        for repo in self._repositories:
            type(repo)
            if not self.config.local_development:
                logging.debug("Installing repository: {}".format(repo))
                repo.install()

        self.helm.repo_update()

        if not self.config.local_development:
            self._compare_required_versions()

    def __str__(self):
        return str(self._dict)

    @property
    def repositories(self):
        """ Course repositories """
        return self._repositories

    def __getattr__(self, key):
        return self._dict.get(key)

    @property
    def charts(self):
        """ List of Chart() instances """
        return self._charts

    def plot(self, charts_to_install):
        """
        Accepts charts_to_install, an interable of the names of the charts
        to install. This method compares the charts in the argument to the 
        charts in the course and calls Chart.install()

        """
        _charts = []
        _failed_charts = []
        self._charts_to_install = []

        try:
            iter(charts_to_install)
        except TypeError:
            charts_to_install = (charts_to_install)

        for chart in self.charts:
            if chart.release_name in charts_to_install:
                self._charts_to_install.append(chart)

        for chart in self._charts_to_install:
            logging.info("Installing {}".format(chart.release_name))
            try:
                chart.install(self.namespace)
            except (Exception, ReckonerCommandException), e:
                if type(e) == ReckonerCommandException:
                    logging.error(e.stderr)
                logging.error('Helm upgrade failed. Rolling back {}'.format(chart.release_name))
                logging.debug(traceback.format_exc())
                chart.rollback
                _failed_charts.append(chart)

        if _failed_charts:
            logging.error("ERROR: Some charts failed to install and were rolled back")
            for chart in _failed_charts:
                logging.error(" - {}".format(chart.release_name))
        return True

    def _compare_required_versions(self):
        """
        Compare installed versions of helm and reckoner to the minimum versions
        required by the course.yml
        Accepts no arguments
        """
        if self.minimum_versions is None:
            return True
        helm_minimum_version = self.minimum_versions.get('helm', '0.0.0')
        reckoner_minimum_version = self.minimum_versions.get('reckoner', '0.0.0')

        logging.debug("Helm Minimum Version is: {}".format(helm_minimum_version))
        logging.debug("Helm Installed Version is {}".format(self.helm.client_version))

        logging.debug("Autohelm Minimum Version is {}".format(reckoner_minimum_version))
        logging.debug("Autohelm Installed Version is {}".format(reckoner_version))

        r1 = semver.compare(reckoner_version, reckoner_minimum_version)
        if r1 < 0:
            raise MinimumVersionException("reckoner Minimum Version {} not met.".format(reckoner_minimum_version))

        if not self.config.local_development:
            r2 = semver.compare(self.helm.client_version, helm_minimum_version)
            if r2 < 0:
                raise MinimumVersionException("helm Minimum Version {} not met.".format(helm_minimum_version))

        return True
