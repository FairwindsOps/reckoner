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


import logging
import semver
import sys
from typing import List

from .config import Config
from .chart import Chart, ChartResult
from .repository import Repository
from .exception import MinimumVersionException, ReckonerCommandException, NoChartsToInstall, ReckonerException
from .helm.client import get_helm_client
from .yaml.handler import Handler as yaml_handler

from io import BufferedReader

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

    def __init__(self, course_file: BufferedReader):
        """
        Parse course.yml contents into instances.
        """
        self.config = Config()
        try:
            self._dict = yaml_handler.load(course_file)
        except Exception as err:
            raise ReckonerException("Error loading the course file: {}".format(err))

        try:
            self.helm = get_helm_client(helm_arguments=self.config.helm_args)
        except Exception as e:
            raise ReckonerException("Helm Client Failed to initialize: {}".format(e))

        self._repositories = []
        self._charts = []
        for name, repository in self._dict.get('repositories', {}).items():
            repository['name'] = name
            self._repositories.append(Repository(repository, self.helm))

        for name, chart in self._dict.get('charts', {}).items():
            self._set_chart_repository(chart)
            self._charts.append(Chart({name: chart}, self.helm))

        for repo in self._repositories:
            # Skip install of repo if it is git based since it will be installed from the chart class
            if repo.git is None:
                logging.debug("Installing repository: {}".format(repo))
                repo.install(chart_name=repo._repository['name'], version=repo._repository.get('version'))
            else:
                logging.debug("Skipping git install of repository to later be installed at the chart level: {}".format(repo))

        self.helm.repo_update()

        try:
            self._compare_required_versions()
        except MinimumVersionException as e:
            logging.error(e)
            sys.exit(1)

    # HACK: This logic is here to try to replace a named reference to a helm repo defined in the main
    #       course repositories. This is because we want to pass the git repo and some
    #       other data to the chart (since the chart also tries to install the repo)
    #
    # NOTE: The real fix here would be to unify the way repositories are installed and managed instead
    #       running the install() function twice from the course.yml and from the charts.yml.
    #
    # IF: chart has a repository definition that is a string reference, then find that
    # reference (if exists) from the main repositories for the course and replace the
    # string definition with the repositories setting.
    def _set_chart_repository(self, chart: dict):
        """_set_chart_repository will convert the string reference of a
        repository into the dictionary configuration of that repository
        or, if None, or if the string isn't in the repositories section,
        it will leave it alone."""
        if isinstance(chart.get('repository', None), str) and chart['repository'] in [x.name for x in self.repositories]:
            logging.debug('Found a reference to a repository installed via repositories section of course, replacing reference.')
            chart['repository'] = self._dict['repositories'][chart['repository']]

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

    def install_charts(self, charts_to_install: list) -> List[ChartResult]:
        results = []
        for chart in charts_to_install:
            logging.info("Installing {}".format(chart.release_name))
            try:
                chart.install(namespace=self.namespace, context=self.context)
            except (Exception, ReckonerCommandException) as e:
                if type(e) == ReckonerCommandException:
                    logging.error(e.stderr)
                if type(e) == Exception:
                    logging.error(e)
                logging.error('Helm upgrade failed on {}'.format(chart.release_name))
                # chart.rollback #TODO Fix this - it doesn't actually fire or work
                logging.error("ERROR: Chart failed to install.")
                logging.error(" - {}".format(chart.release_name))
                if not self.config.continue_on_error:
                    logging.error("Stopping chart installations due to an error! Some of your charts may not have been installed!")
                    break
            finally:
                # Always grab any results in the chart results
                results.append(chart.result)

        return results

    def plot(self, charts_requested_to_install: list) -> List[ChartResult]:
        """
        Accepts charts_to_install, an interable of the names of the charts
        to install. This method compares the charts in the argument to the
        charts in the course and calls Chart.install()

        """
        self._charts_to_install = []
        # NOTE: Unexpected feature here: Since we're iterating on all charts
        #       in the course to find the ones the user has requested, a
        #       byproduct is that the --only's will always be run in the order
        #       defined in the course.yml. No matter the order added to via
        #       command line arguments.
        for chart in self.charts:
            if chart.release_name in charts_requested_to_install:
                self._charts_to_install.append(chart)
                charts_requested_to_install.remove(chart.release_name)
            else:
                logging.debug(
                    'Skipping {} in course.yml, not found '
                    'in your requested charts list'.format(chart.release_name)
                )
        # If any items remain in charts requested - warn that we didn't find them
        self._warn_about_missing_requested_charts(charts_requested_to_install)

        # Check to assure out install list has charts in it
        self._check_for_empty_install_list(charts_requested_to_install)

        # return the results of the charts installation
        return self.install_charts(self._charts_to_install)

    def _check_for_empty_install_list(self, requested_charts):
        if len(self._charts_to_install) == 0:
            raise NoChartsToInstall(
                'None of the charts you requested to install ({}) could be '
                'found in the course list. Verify you are using the '
                'release-name and not the chart name.'.format(', '.join(requested_charts))
            )

    def _warn_about_missing_requested_charts(self, charts_which_were_not_found):
        if charts_which_were_not_found:
            for missing_chart in charts_which_were_not_found:
                logging.warning(
                    'Could not find {} in course.yml'.format(missing_chart)
                )
            logging.warning('Some of the requested charts were not found in '
                            'your course.yml')

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
        logging.debug("Helm Installed Version is {}".format(self.helm.version))

        logging.debug("Reckoner Minimum Version is {}".format(reckoner_minimum_version))
        logging.debug("Reckoner Installed Version is {}".format(reckoner_version))

        r1 = semver.compare(reckoner_version, reckoner_minimum_version)
        if r1 < 0:
            raise MinimumVersionException("reckoner Minimum Version {} not met.".format(reckoner_minimum_version))

        r2 = semver.compare(self.helm.version, helm_minimum_version)
        if r2 < 0:
            raise MinimumVersionException("helm Minimum Version {} not met.".format(helm_minimum_version))

        return True
