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


import os
import logging
from os.path import dirname

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

    def __init__(self):
        self.__dict__ = self._config
        self._installed_repositories = []

    @property
    def home(self):
        """ Helm home path """
        if self._config.get("home") is None:
            helm_home = os.environ.get('HELM_HOME')
            fallback_home = os.environ.get('HOME') + "/.helm"
            if helm_home is not None:
                self._config['home'] = helm_home
            else:
                self._config['home'] = fallback_home
                logging.warn("$HELM_HOME not set. Using ~/.helm")

        return self._config['home']

    @property
    def archive(self):
        """ Helm archive path """
        if 'archive' not in self._config:
            archive = self.home + '/cache/archive'
            if not os.path.isdir(archive):
                logging.warn("{} does not exist. Have you run `helm init`?".format(archive))
            self._config['archive'] = archive

        return self._config['archive']

    @property
    def course_base_directory(self):
        return dirname(self.course_path) or None

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
