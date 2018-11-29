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
import re
import git
import os
import sys

from . import call
from config import Config
from exception import ReckonerCommandException
from git import GitCommandError


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
                self._repository['path'] = repository.get('path')

    def __getattr__(self, key):
        return self._repository.get(key)

    def __str__(self):
        return str(self._repository)

    def __eq__(self, other):
        return self._repository == other._repository

    @property
    def chart_path(self):
        return self._chart_path

    def install(self, chart_name=None, version=None):
        """ Install Helm repository """
        from helm import Helm  # currently cheating to get around a circular import issue

        helm = Helm()
        if self.git is None:
            self._chart_path = "{}/{}".format(self.name, chart_name)
            if self.name not in [repository.name for repository in helm.repositories]:
                try:
                    return helm.repo_add(str(self.name), str(self.url))
                except ReckonerCommandException, e:
                    logging.warn("Unable to install repository {}: {}".format(self.name, e.stderr))
                    return False
            else:
                logging.debug("Chart repository {} already installed".format(self.name))
                return True
        else:
            if version is None:
                version = 'master'

            if self.path is None:
                self.path = ''

            self.name = '{}/{}/{}/{}' .format(
                self.config.archive,
                re.sub(
                    r'\:\/\/|\/|\.', '_',
                    self.git
                ),
                chart_name,
                self.path or '')

            self._fetch_from_git(chart_name, version)

            # If the chart_name is in the repo path and appears to be redundant pb
            if os.path.isfile("{}/Chart.yaml".format(self.chart_path)):
                return True

            if self.chart_path.endswith(chart_name):
                self._chart_path = self.chart_path[:-len(chart_name) - 1]
                if os.path.isfile("{}/Chart.yaml".format(self.chart_path)):
                    return True

    def _fetch_from_git(self, chart_name, version):
        """ Does a sparse checkout for a git repository git_repo@branch and retrieves the chart at the path """

        def fetch_pull(ref):
            """ Do the fetch, checkout pull for the git ref """
            origin.fetch(tags=True)
            repo.git.checkout("{}".format(ref))
            repo.git.pull("origin", "{}".format(ref))

        repo_path = '{}/{}'.format(
            self.config.archive,
            re.sub(r'\:\/\/|\/|\.', '_', self.git)
        )

        logging.debug('Chart repository path: {}'.format(repo_path))
        if not os.path.isdir(repo_path):
            os.makedirs(repo_path)

        if not os.path.isdir("{}/.git".format(repo_path)):
            repo = git.Repo.init(repo_path)
        else:
            repo = git.Repo(repo_path)

        sparse_checkout_file_path = "{}/.git/info/sparse-checkout".format(repo_path)

        # A path in the list implies that the Chart is at the root of the git repository.
        if self.path not in ['', '/', './', None]:
            self._chart_path = "{}/{}\n".format(self.path, chart_name)
            repo.git.config('core.sparseCheckout', 'true')
            with open(sparse_checkout_file_path, "ab+") as scf:
                if self.path not in scf.readlines():
                    scf.write(self._chart_path)
            logging.debug("Configuring sparse checkout for path: {}".format(self.path))

        self._chart_path = "{}/{}/{}".format(repo_path, self.path, chart_name)

        logging.debug("Chart path: {} ".format(self.chart_path))

        if not self.config.local_development:
            if 'origin' in [remote.name for remote in repo.remotes]:
                origin = repo.remotes['origin']
            else:
                origin = repo.create_remote('origin', (self.git))

            try:
                fetch_pull(version)
            except GitCommandError, e:
                logging.warn(e)
                if 'Sparse checkout leaves no entry on working directory' in str(e):
                    logging.warn("Error with path \"{}\"! Remove path when chart exists at the repository root".format(self.path))
                    logging.warn("Skipping chart {}".format(chart_name))
                    return False
                elif 'did not match any file(s) known to git.' in str(e):
                    logging.warn("Branch/tag \"{}\" does not seem to exist!".format(version))
                    logging.warn("Skipping chart {}".format(chart_name))
                    return False
                else:
                    logging.error(e)
                    raise e
            except Exception, e:
                logging.error(e)
                raise e
            finally:
                # Remove sparse-checkout to prevent path issues from poisoning the cache
                logging.debug("Removing sparse checkout config")
                if os.path.isfile(sparse_checkout_file_path):
                    os.remove(sparse_checkout_file_path)
                repo.git.config('core.sparseCheckout', 'false')
