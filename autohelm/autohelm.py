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
import sys

from . import call
from config import Config
from course import Course
from exception import AutoHelmException


class AutoHelm(object):

    def __init__(self, file=None, dryrun=False, debug=False, helm_args=None, local_development=False):

        self.config = Config()
        self.config.dryrun = dryrun
        self.config.debug = debug
        self.config.helm_args = helm_args
        self.config.local_development = local_development
        self.course = Course(file)

    def install(self, charts=[]):
        """
        Calls plot on course instance. Accepts list or tuple that is the keys
        of the charts dictionary. Only that list of charts will be installed or
        if the argument is emmpty, All charts in the course will be installed
        """
        if not self._environment_has_requirements:
            raise AutoHelmException("Error running install of autohelm, please see errors above.")

        selected_charts = charts or [chart._release_name for chart in self.course.charts]
        return self.course.plot(selected_charts)

    def _update_context(self):
        """
        Update the current context in the kubeconfig to the desired context
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
            raise AutoHelmException("Unable to set cluster context to: {}".format(self._context))

    @property
    def _environment_has_requirements(self):
        if self.config.tiller_present:
            return True
        else:
            logging.error("Tiller not present in cluster. Have you run `helm init`?")
            return False
