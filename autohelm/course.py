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
import autohelm

import oyaml as yaml

from config import Config
from chart import Chart
from repository import Repository
from exception import MinimumVersionException

from meta import __version__ as autohelm_version


class Course(object):

    def __init__(self, file):
        self.config = Config()
        self._dict = yaml.load(file)
        logging.debug(self._dict)
        self._repositories = []
        for name, repository in self._dict.get('repositories', {}).iteritems():
            repository['name'] = name
            self._repositories.append(Repository(repository))

        for repo in self.repositories:
            if not self.config.local_development:
                repo.install()
                repo.update()

        self._compare_required_versions()
        self._charts = []

    def __str__(self):
        return str(self._dict)

    @property
    def repositories(self):
        return self._repositories

    @property
    def charts(self):
        if self._charts == []:
            for name, chart in self._dict['charts'].iteritems():
                self._charts.append(Chart({name: chart}))

        return self._charts

    def __getattr__(self, key):
        return self._dict.get(key)

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
            if chart.name in charts_to_install:
                self._charts_to_install.append(chart)

        for chart in self._charts_to_install:
            logging.debug("Installing {}".format(chart.name))

            if not chart.install(self.namespace):
                logging.error('Helm upgrade failed on {}. Rolling back...'.format(chart))
                chart.rollback
                failed_charts.append(chart)

        if _failed_charts:
            logging.error("ERROR: Some charts failed to install and were rolled back")
            for chart in failed_charts:
                logging.error(" - {}".format(chart))
            raise
            sys.exit(1)

        return True

    def _compare_required_versions(self):
        """
        Compare installed versions of helm and autohelm to the minimum versions
        required by the course.yml
        Accepts no arguments
        """
        if self.minimum_versions is None:
            return True
        helm_minimum_version = self.minimum_versions.get('helm', '0.0.0')
        autohelm_minimum_version = self.minimum_versions.get('autohelm', '0.0.0')

        logging.debug("Helm Minimum Version is: {}".format(helm_minimum_version))
        logging.debug("Helm Installed Version is {}".format(self.config.helm_version))

        logging.debug("Autohelm Minimum Version is {}".format(autohelm_minimum_version))
        logging.debug("Autohelm Installed Version is {}".format(autohelm_version))

        r1 = semver.compare(autohelm_version, autohelm_minimum_version)
        if r1 < 0:
            raise MinimumVersionException("autohelm Minimum Version {} not met.".format(autohelm_minimum_version))
        r2 = semver.compare(self.config.helm_version, helm_minimum_version)
        if r2 < 0:
            raise MinimumVersionException("helm Minimum Version {} not met.".format(helm_minimum_version))

        return True
