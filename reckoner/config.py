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


import os
import logging
from os.path import dirname, abspath

from .command_line_caller import call


class Config(object):
    """
    Description:
    - Following the borg pattern, this class is used by all other classes to
      share default and top level config setting between instances

    Arguments:
    - None

    Attributes:
    - home (String): Defaults to "$HOME/.helm" but is overridden by
      environment variable $HELM_HOME
    - archive (String): Interpolated path for the helm archive

    """
    _config = {}

    @classmethod
    def reset(cls):
        cls._config = {}

    def __init__(self):
        self.__dict__ = self._config
        self._installed_repositories = []
        self.continue_on_error = self._config.get('continue_on_error')

    @property
    def course_base_directory(self):
        if self.course_path:
            return dirname(abspath(self.course_path))
        else:
            return '.'

    @property
    def update_repos(self):
        if self.__dict__.get('update_repos') is not None:
            return self.__dict__.get('update_repos')
        else:
            return True

    @update_repos.setter
    def update_repos(self, value):
        self.__dict__['update_repos'] = bool(value)

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)

    def __str__(self):
        return str(self._config)

    def __iter__(self):
        return iter(self._config)

    def __getattr__(self, key):
        return self._config.get(key)

    @property
    def current_context(self):
        """ Returns the current cluster context """
        args = ['kubectl', 'config', 'current-context']
        r = call(args)
        return r.stdout.strip()
