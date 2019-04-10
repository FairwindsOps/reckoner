# -- coding: utf-8 --

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


import logging
import semver
import traceback
import sys

import oyaml as yaml

from .config import Config
from .chart import Chart
from .repository import Repository
from .exception import MinimumVersionException, ReckonerCommandException, NoChartsToInstall
from .helm.client import HelmClient

from .meta import __version__ as reckoner_version


class Course(object):
    """
    Description:
    - Top level class for the attributes of the course.yml file
    - Parses yaml file into various Reckoner classes

    Arguments:
    - file (File)

    Attributes:
    - config: Instance of Config()
    - helm: Instance of HelmClient()
    - charts: List of Chart() instances
    - repositories: List of Repository() instances

    """

    def __init__(self, course_file):
        """
        Parse course.yml contents into instances.
        """
        self.config = Config()
        self._dict = yaml.load(course_file, Loader=yaml.loader.FullLoader)
        if not self.config.helm_args:
            self.config.helm_args = self._dict.get('helm_args')
        self.helm = HelmClient(default_helm_arguments=self.config.helm_args)
        self._repositories = []
        self._charts = []
        self._failed_charts = []
        for name, repository in self._dict.get('repositories', {}).items():
            repository['name'] = name
            self._repositories.append(Repository(repository, self.helm))

        for name, chart in self._dict.get('charts', {}).items():
            self._charts.append(Chart({name: chart}, self.helm))

        for repo in self._repositories:
            type(repo)
            if not self.config.local_development:
                logging.debug("Installing repository: {}".format(repo))
                repo.install()

        self.helm.repo_update()

        if not self.config.local_development:
            try:
                self._compare_required_versions()
            except MinimumVersionException as e:
                logging.error(e)
                sys.exit(1)

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

    @property
    def failed_charts(self):
        return self._failed_charts

    def plot(self, charts_to_install):
        """
        Accepts charts_to_install, an interable of the names of the charts
        to install. This method compares the charts in the argument to the
        charts in the course and calls Chart.install()

        """
        self._charts_to_install = []

        try:
            iter(charts_to_install)
        except TypeError:
            charts_to_install = charts_to_install

        for chart in self.charts:
            if chart.release_name in charts_to_install:
                self._charts_to_install.append(chart)
                charts_to_install.remove(chart.release_name)
            else:
                logging.debug(
                    'Skipping {} in course.yml, not found '
                    'in your requested charts list'.format(chart.release_name)
                )

        if len(self._charts_to_install) == 0:
            raise NoChartsToInstall(
                'No charts found from requested list ({}). They do not exist '
                'in the course.yml. Verify you are using the release-name '
                'and not the chart name.'.format(', '.join(charts_to_install))
            )

        for chart in self._charts_to_install:
            logging.info("Installing {}".format(chart.release_name))
            try:
                chart.install(namespace=self.namespace, context=self.context)
            except (Exception, ReckonerCommandException) as e:
                if type(e) == ReckonerCommandException:
                    logging.error(e.stderr)
                if type(e) == Exception:
                    logging.error(e)
                logging.error('Helm upgrade failed on {}'.format(chart.release_name))
                logging.debug(traceback.format_exc())
                # chart.rollback #TODO Fix this - it doesn't actually fire or work
                self.failed_charts.append(chart)

        if self.failed_charts:
            logging.error("ERROR: Some charts failed to install.")
            for chart in self.failed_charts:
                logging.error(" - {}".format(chart.release_name))

        if charts_to_install:
            for missing_chart in charts_to_install:
                logging.warning(
                    'Could not find {} in course.yml'.format(missing_chart)
                )
            logging.warning('Some of the requested charts were not found in '
                            'your course.yml')

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

        logging.debug("Reckoner Minimum Version is {}".format(reckoner_minimum_version))
        logging.debug("Reckoner Installed Version is {}".format(reckoner_version))

        r1 = semver.compare(reckoner_version, reckoner_minimum_version)
        if r1 < 0:
            raise MinimumVersionException("reckoner Minimum Version {} not met.".format(reckoner_minimum_version))

        if not self.config.local_development:
            r2 = semver.compare(self.helm.client_version, helm_minimum_version)
            if r2 < 0:
                raise MinimumVersionException("helm Minimum Version {} not met.".format(helm_minimum_version))

        return True
