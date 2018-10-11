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
    """
    Description:
    - Helm repository object

    Arguments:
    - name: repostiory name
    - url: tgz reppsitory url
    - git: git repository url
    - path: path in git repository
    """

    def __init__(self, repository):
        super(type(self), self).__init__()
        self.config = Config()
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

    def __eq__(self, other):
        return self._repository == other._repository

    def install(self):
        """ Install Helm repository """
        # TODO: Sort out imports so that Helm() can be imported here.
        # autohelm.helm imports autohelm.repository (this file) and
        # I couldn't figure out a way to avoid the circular import
        # fairly quickly so I dropped it here an moved on for the
        # time being.

        from helm import Helm
        helm = Helm()

        if self.git is None:
            if self not in helm.repositories:
                try:
                    return helm.repo_add(str(self.name), str(self.url))
                except AutoHelmCommandException, e:
                    logging.warn("Unable to install repository {}: {}".format(self.name, e.stderr))
                    return False
            else:
                logging.debug("Chart repository {} already installed".format(self.name))
                return True
