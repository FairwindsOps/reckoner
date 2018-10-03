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

from . import call
from config import Config
from exception import AutoHelmCommandException

class Repository(object):

    def __init__(self, repository):
        super(type(self), self).__init__()
        self.config = Config()
        logging.debug("Repository: {}".format(repository))
        self._repository = {}
        if type(repository) is str:
            self._repository['name'] = repository
        else:
            if repository.get('name'):
                self._repository['name'] = repository.get('name')
            if repository.get('url'):
                self._repository['url'] = repository.get('url')
            if repository.get('git'):
                self._repository['git'] = repository.get('git')
            if repository.get('path'):
                self._repository['path'] = repository.get('path', '')

    def __getattr__(self, key):
        return self._repository.get(key)

    def __str__(self):
        return str(self._repository)

    def install(self):
        """ Install Helm repository """
        from helm import Helm #currently cheating to get around a circular import issue
        helm = Helm()
        logging.debug("Installing Chart Repository: {}".format(self.name))

        if self.git is None:
            if self._repository not in helm.repositories:
                try:
                    return helm.repo_add(str(self.name),str(self.url))
                except AutoHelmCommandException, e:
                    logging.warn("Unable to install repository {}: {}".format(self.name,e.stderr) )
                    return False
            else:
                logging.debug("Chart repository {} already installed".format(self.name))
                return True
