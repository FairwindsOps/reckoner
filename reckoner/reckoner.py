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

"""Reckoner object"""

import logging
import sys

from .config import Config
from .course import Course
from .helm.client import HelmClient, HelmClientException
from .exception import NoChartsToInstall, ReckonerCommandException


class Reckoner(object):
    """
    Description:
    - Core Reckoner class

    Arguments:
    - file(file object) - file object of the course.yml
    - dryrun (bool) - implies helm --dry-run --debug and skips any hooks
    - debug (bool) DEPRECATED - use helm_args instead or just --dry-run
    - helm_args (list) - passes content of list as additional arguments to helm binary
    - local_development (bool) - when true, most actions over the network are switched off

    Attributes:
    - config: Instance of Config()
    - helm: Instance of HelmClient()
    - course: Instance of Course()

    """

    def __init__(self, course_file=None, dryrun=False, debug=False, helm_args=None, local_development=False):
        self.config = Config()
        self.config.dryrun = dryrun
        self.config.debug = debug
        self.config.local_development = local_development
        self.config.helm_args = helm_args
        if course_file:
            self.config.course_path = course_file.name

        if self.config.debug:
            logging.warn("The --debug flag will be deprecated.  Please use --helm-args or --dry-run instead.")
        if self.config.helm_args:
            logging.warn("Specifying --helm-args on the cli will override helm_args in the course file.")

        try:
            self.helm = HelmClient(default_helm_arguments=self.config.helm_args)
        except Exception as e:
            logging.error(e)
            sys.exit(1)

        if not self.config.local_development:
            try:
                self.helm.check_helm_command()
                self.helm.server_version
            except HelmClientException as e:
                logging.error("Failed checking helm: See errors:\n{}".format(e))
                sys.exit(1)

        self.course = Course(course_file)

    def install(self, charts=[]):
        """
        Description:
        - Calls plot on course instance.

        Arguments:
        - charts (default: []): list or tuple of release_names from the course. That list of
          charts will be installed or if the argument is empty, All charts in the course will be installed

        Returns:
        - bool

        """
        selected_charts = charts or [chart._release_name for chart in self.course.charts]
        try:
            self.course.plot(selected_charts)
        except NoChartsToInstall as error:
            logging.error(error)
            raise ReckonerCommandException('Failed to find any valid charts to install.')

        # HACK - Nick Huanca
        # This is to satisfy a test requirement but the bool contract is a
        # farse. The called plot command only ever raised an error or returned
        # True. Having this always return True doesn't make sense and needs to
        # be refactored to either have logic for WHY you want True or False.
        # The upstream use of this code doesn't do anything with the return
        # values of this function. (reckoner.cli.plot)
        # The Tests:
        #   - TestReckonerMethods.test_install_succeeds
        #   - TestReckoner.test_install
        return True

    # TODO this doesn't actually work to update context - missing _context attribute.
    #      also missing subprocess function
    def _update_context(self):
        """
        Description:
        - Update the current context in the kubeconfig to the desired context.
          Accepts no arguments
        """
        logging.debug("Checking for correct cluster context")
        logging.debug("Current cluster context is: {}".format(self.config.current_context))

        self.course.context or self.config.current_context
        if self.config.local_development:
            return True

        if self.config.current_context != self._context:
            logging.debug("Updating cluster context to {}".format(self._context))
            args = ['kubectl', 'config', 'use-context', self._context]
            logging.debug(" ".join(args))
            subprocess.call(args)

        if self.config.current_context == self._context:
            return True
        else:
            raise ReckonerException("Unable to set cluster context to: {}".format(self._context))
