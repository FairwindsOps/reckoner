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

import traceback
import logging
import semver
import sys
import os
from typing import List

from .hooks import Hook
from .config import Config
from .repository import Repository
from .chart import Chart, ChartResult
from .secrets import Secret
from .helm.client import get_helm_client
from .yaml.handler import Handler as yaml_handler
from .meta import __version__ as reckoner_version
from .exception import MinimumVersionException, ReckonerCommandException, NoChartsToInstall, ReckonerException

from io import BufferedReader


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

        # Send entire dictionary of the secret as kwargs
        self._secrets = []
        for secret in self._dict.get('secrets', []):
            self._secrets.append(Secret(**secret))

        for name, chart in self._dict.get('charts', {}).items():
            self._set_chart_repository(chart)
            self._charts.append(Chart({name: chart}, self.helm))

        # Parsing and prepping hooks from course.yml
        self._hooks = self._dict.get('hooks', {})
        self._pre_install_hook = Hook(
            self.hooks.get(
                'pre_install',
                []
            ),
            'Course pre install',
            self.config.course_base_directory
        )

        self._post_install_hook = Hook(
            self.hooks.get(
                'post_install',
                []
            ),
            'Course post install',
            self.config.course_base_directory
        )

        self._init_hook = Hook(
            self.hooks.get(
                'init',
                []
            ),
            'Course Init',
            self.config.course_base_directory
        )

        # Run Init hook before we do anything other than parse the course
        self.init_hook.run()

        if self.config.update_repos:
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

    @property
    def secrets(self):
        """ Secrets Defined in the Chart """
        return self._secrets

    @property
    def namespace_management(self):
        """ The default namespace manager block from the course if it exists
        Otherwise, returns {} """
        _namespace_management = self._dict.get('namespace_management')

        if _namespace_management is None:
            return {}
        else:
            return _namespace_management.get('default', {})

    def __getattr__(self, key):
        return self._dict.get(key)

    @property
    def hooks(self):
        return self._hooks

    @property
    def charts(self):
        """ List of Chart() instances """
        return self._charts

    @property
    def pre_install_hook(self):
        return self._pre_install_hook

    @property
    def post_install_hook(self):
        return self._post_install_hook

    @property
    def init_hook(self):
        return self._init_hook

    def merge_secrets_into_environment(self) -> None:
        """
        Accepts no Argument
        Returns None

        Loops over list of secrets and merges the name:values into the environment
        Throws ReckonerException if there is an existing Environment of the same name
        """

        for secret in self.secrets:
            if secret.name in os.environ.keys():
                raise ReckonerException(
                    f"Found Secret {secret.name} with the same name as existing environment variable. "
                    "Secrets may not have the same name as and existing environment variable"
                )
            try:
                os.environ[secret.name] = secret.value
            except Exception as e:
                logging.error(f"Error retrieving value of secret {secret.name}")
                logging.debug(traceback.format_exc())
                raise e

    def __run_command_for_charts_list(self, command: str, charts: list) -> List[ChartResult]:
        results = []
        self.merge_secrets_into_environment()
        for chart in charts:
            namespace = chart.namespace or self.namespace
            logging.info(f"Running '{command}' on {chart.release_name} in {namespace}")
            try:
                getattr(chart, command)(
                    default_namespace=self.namespace,
                    default_namespace_management=self.namespace_management,
                    context=self.context
                )
            except (Exception, ReckonerCommandException) as e:
                logging.debug(traceback.format_exc())
                if type(e) == ReckonerCommandException:
                    logging.error(e.stderr)
                if type(e) == Exception:
                    logging.error(e)
                logging.error(f'ERROR: {command} Failed on {chart.release_name}')
                if not self.config.continue_on_error:
                    logging.error(str(e))
                    raise ReckonerCommandException(
                        f"Stopping '{command}' for chart due to an error!"
                        " Some of your requested actions may not have been"
                        " completed!") from None
            finally:
                # Always grab any results in the chart results
                results.append(chart.result)
        return results

    def install_charts(self, charts_to_install: list) -> List[ChartResult]:
        """
        For a list of charts_to_install, run the `install` method on each chart instance.
        Accepts list of `Chart()`
        Returns list of `ChartResult()`
        """
        return self.__run_command_for_charts_list('install', charts_to_install)

    def update_charts(self, charts_to_update: list) -> List[ChartResult]:
        """
        For a list of charts_to_update, run the `update` method on each chart instance.
        Accepts list of `Chart()`
        Returns list of `ChartResult()`
        """
        return self.__run_command_for_charts_list('update', charts_to_update)

    def template_charts(self, charts_to_template: list) -> List[ChartResult]:
        """
        For a list of charts_to_install, run the `template` method on each chart instance
        Accepts list of `Chart()`
        Returns list of `ChartResult()`
        """
        return self.__run_command_for_charts_list('template', charts_to_template)

    def get_chart_manifests(self, charts_to_manifest: list) -> List[ChartResult]:
        """
        For a list of charts_to_install, run the `get_manifest` method on each chart instance
        Accepts list of `Chart()`
        Returns list of `ChartResult()`
        """
        return self.__run_command_for_charts_list('get_manifest', charts_to_manifest)

    def diff_charts(self, charts_to_diff: list) -> List[ChartResult]:
        """
        For a list of charts_to_install, run the `get_manifest` method on each chart instance
        Accepts list of `Chart()`
        Returns list of `ChartResult()`
        """
        return self.__run_command_for_charts_list('diff', charts_to_diff)

    def only_charts(self, charts_requested: list) -> List[str]:
        """
        Accepts the list of requested charts, compares that to the course
        return the intersection. Will log if chart is requested but not
        present in the chart
        """
        self._only_charts = []

        # NOTE: Unexpected feature here: Since we're iterating on all charts
        #       in the course to find the ones the user has requested, a
        #       byproduct is that the --only's will always be run in the order
        #       defined in the course.yml. No matter the order added to via
        #       command line arguments.

        for chart in self.charts:
            if chart.release_name in charts_requested:
                self._only_charts.append(chart)
                charts_requested.remove(chart.release_name)
            else:
                logging.debug(
                    'Skipping {} in course.yml, not found '
                    'in your requested charts list'.format(chart.release_name)
                )

        # If any items remain in charts requested - warn that we didn't find them
        self._warn_about_missing_requested_charts(charts_requested)

        if len(self._only_charts) == 0:
            raise NoChartsToInstall(
                'None of the charts you requested ({}) could be '
                'found in the course list. Verify you are using the '
                'release-name and not the chart name.'.format(', '.join(charts_requested))
            )

        return self._only_charts

    def template(self, charts_requested_to_template: list) -> List[str]:
        """
        Accepts charts_requested_to_template, an iterable of the names of the charts
        to template. This method compares the charts in the argument to the
        charts in the course and calls Chart.template()

        """
        # return the text of the charts templating
        results = self.template_charts(self.only_charts(charts_requested_to_template))
        return results

    def get_manifests(self, charts_manifests_requested: list) -> List[str]:
        """
        Accepts charts_manifests_requested, an iterable of the names of the charts
        to get manifests for. This method compares the charts in the argument to the
        charts in the course and calls Chart.get_manifest()

        """
        # return the text of the charts templating
        results = self.get_chart_manifests(self.only_charts(charts_manifests_requested))
        return results

    def diff(self, chart_diffs_requested: list) -> List[str]:
        """
        Accepts chart_diffs_requested, an iterable of the names of the charts
        to get manifests for. This method compares the charts in the argument to the
        charts in the course and calls Chart.diff()

        """
        # return the text of the charts templating
        results = self.diff_charts(self.only_charts(chart_diffs_requested))
        return results

    def plot(self, charts_requested_to_install: list) -> List[ChartResult]:
        """
        Accepts charts_to_install, an iterable of the names of the charts
        to install. This method compares the charts in the argument to the
        charts in the course and calls Chart.install()

        """
        # return the results of the charts installation, exit on error to prevent post install hook run
        self.pre_install_hook.run()
        results = self.install_charts(self.only_charts(charts_requested_to_install))
        for chart in results:
            if chart.failed == True and not self.config.continue_on_error:
                logging.error("Not running Course post_install hook due to a chart install error!")
                return results

        self.post_install_hook.run()
        return results

    def update(self, charts_requested_to_update: list) -> List[ChartResult]:
        """
        Accepts charts_to_update, an iterable of the names of the charts
        to update. This method compares the charts in the argument to the
        charts in the course and calls Chart.update()

        """
        # return the results of the charts update, exit on error to prevent post install hook run
        self.pre_install_hook.run()
        results = self.update_charts(self.only_charts(charts_requested_to_update))
        for chart in results:
            if chart.failed == True and not self.config.continue_on_error:
                logging.error("Not running Course post_install hook due to a chart install error!")
                return results

        self.post_install_hook.run()
        return results

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
