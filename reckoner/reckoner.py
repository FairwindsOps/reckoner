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

"""Reckoner object"""

import logging
from typing import List

from .config import Config
from .course import Course
from .chart import ChartResult
from .exception import NoChartsToInstall, ReckonerCommandException, ReckonerException
from io import BufferedReader


class ReckonerInstallResults:
    def __init__(self):
        self.results = []

    def add_result(self, result: ChartResult) -> None:
        self.results.append(result)

    @property
    def has_errors(self) -> bool:
        if any([result.failed for result in self.results]):
            return True
        else:
            return False

    @property
    def results_with_errors(self) -> List[ChartResult]:
        return [result for result in self.results if result.failed]


class Reckoner(object):
    """
    Description:
    - Core Reckoner class

    Arguments:
    - file(file object) - file object of the course.yml
    - dryrun (bool) - implies helm --dry-run --debug and skips any hooks
    - debug (bool) DEPRECATED - use helm_args instead or just --dry-run
    - helm_args (list) - passes content of list as additional arguments to helm binary

    Attributes:
    - config: Instance of Config()
    - helm: Instance of HelmClient()
    - course: Instance of Course()

    """

    def __init__(self, course_file: BufferedReader = None, dryrun=False, debug=False, helm_args=None, continue_on_error=False, create_namespace=True):
        self.config = Config()
        self.results = ReckonerInstallResults()
        self.config.dryrun = dryrun
        self.config.debug = debug
        self.config.helm_args = helm_args
        self.config.continue_on_error = continue_on_error
        self.config.create_namespace = create_namespace
        if course_file:
            self.config.course_path = course_file.name

        if self.config.debug:
            logging.warn("The --debug flag will be deprecated.  Please use --helm-args or --dry-run instead.")
        if self.config.helm_args:
            logging.warn("Specifying --helm-args on the cli will override helm_args in the course file.")

        self.course = Course(course_file)

    def install(self, charts: List[str] = []) -> None:
        """
        Description:
        - Calls plot on course instance.

        Arguments:
        - charts (default: []): list or tuple of release_names from the course. That list of
          charts will be installed or if the argument is empty, All charts in the course will be installed

        Returns:
        - None

        """
        selected_charts = charts or [chart._release_name for chart in self.course.charts]
        try:
            plot_results = self.course.plot(selected_charts)
            for chart_result in plot_results:
                if chart_result:
                    self.add_result(chart_result)
                else:
                    raise Exception("Didn't expect None as a chart result...")
        except NoChartsToInstall as error:
            logging.error(error)
            raise ReckonerCommandException('Failed to find any valid charts to install.')

    def update(self, charts: List[str] = []) -> None:
        """
        Description:
        - Calls update on course instance.

        Arguments:
        - charts (default: []): list or tuple of release_names from the course. That list of
          charts will be installed or if the argument is empty, All charts in the course will be installed

        Returns:
        - None

        """
        selected_charts = charts or [chart._release_name for chart in self.course.charts]
        try:
            plot_results = self.course.update(selected_charts)
            for chart_result in plot_results:
                if chart_result:
                    self.add_result(chart_result)
                else:
                    raise Exception("Didn't expect None as a chart result...")
        except NoChartsToInstall as error:
            logging.error(error)
            raise ReckonerCommandException('Failed to find any valid charts to install.')

    def template(self, charts: List[str] = []):
        selected_charts = charts or [chart._release_name for chart in self.course.charts]
        try:
            return self.course.template(selected_charts)
        except NoChartsToInstall as error:
            logging.error(error)
            raise ReckonerCommandException('Failed to find any valid charts to template.')

    def get_manifests(self, charts: List[str] = []):
        selected_charts = charts or [chart._release_name for chart in self.course.charts]
        try:
            return self.course.get_manifests(selected_charts)
        except NoChartsToInstall as error:
            logging.error(error)
            raise ReckonerCommandException('Failed to find any valid charts to show manifests for.')

    def diff(self, charts: List[str] = []):
        selected_charts = charts or [chart._release_name for chart in self.course.charts]
        try:
            return self.course.diff(selected_charts)
        except NoChartsToInstall as error:
            logging.error(error)
            raise ReckonerCommandException('Failed to find any valid charts to show diff for.')

    def add_result(self, result: ChartResult) -> None:
        self.results.add_result(result)

    # TODO this doesn't actually work to update context - missing _context attribute.
    #      also missing subprocess function

    # def _update_context(self):
    #     """
    #     Description:
    #     - Update the current context in the kubeconfig to the desired context.
    #       Accepts no arguments
    #     """
    #     logging.debug("Checking for correct cluster context")
    #     logging.debug("Current cluster context is: {}".format(self.config.current_context))

    #     self.course.context or self.config.current_context

    #     if self.config.current_context != self._context:
    #         logging.debug("Updating cluster context to {}".format(self._context))
    #         args = ['kubectl', 'config', 'use-context', self._context]
    #         logging.debug(" ".join(args))
    #         subprocess.call(args)

    #     if self.config.current_context == self._context:
    #         return True
    #     else:
    #         raise ReckonerException("Unable to set cluster context to: {}".format(self._context))
