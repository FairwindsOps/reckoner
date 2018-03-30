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

import oyaml as yaml
import subprocess
import logging
import git
import os
import sys
import re


class AutoHelm(object):

    _default_namespace = 'kube-system'
    _default_repository = 'stable'

    def __init__(self, file=None):

        self._home = os.environ.get('HELM_HOME')
        if self._home is None:
            self._home = os.environ.get('HOME') + "/.helm"
            logging.warn("$HELM_HOME not set. Using ~/.helm")

        self._archive = self._home + '/cache/archive'
        if not os.path.isdir(self._archive):
            logging.error("{} does not exist. Have you run `helm init`?".format(self._archive))
            sys.exit()

        if not self.tiller_present:
            logging.error("Tiller not present in cluster. Have you run `helm init`?")
            sys.exit()

        plan = yaml.load(file)

        self._charts = plan.get('charts')

        self._namespace = plan.get('namespace', self._default_namespace)
        self._repository = plan.get('repository', self._default_repository)
        self._installed_repositories = None

        self._repositories = plan.get('repositories')
        if self._repositories:
            for repo in self._repositories:
                if repo not in self.installed_repositories:
                    url = self._repositories[repo].get('url')
                    self._intall_repository(repo, url)

    @property
    def installed_repositories(self):
        if self._installed_repositories:
            return self._installed_repositories
        else:
            args = ['helm', 'repo', 'list']
            self._installed_repositories = [line.split()[0] for line in subprocess.check_output(args).split('\n')[1:-1]]
            return self._installed_repositories

    @property
    def tiller_present(self):
        """Detects if tiller is present in the currently configured cluster"""
        try:
            FNULL = open(os.devnull, 'w')
            subprocess.check_call(['helm', 'list'], stdout=FNULL, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            return False
        return True

    def _update_repositories(self):
        args = ['helm', 'repo', 'update']
        logging.debug(" ".join(args))
        subprocess.call(args)

    def _intall_repository(self, name, url):
        args = ['helm', 'repo', 'add', name, url]
        logging.debug(" ".join(args))
        subprocess.call(args)

    def _fetch_git_chart(self, name, git_repo, branch, path):

        repo_path = '{}/{}'.format(self._archive, re.sub(r'\:\/\/|\/|\.', '_', git_repo))
        if not os.path.isdir(repo_path):
            os.mkdir(repo_path)

        if not os.path.isdir("{}/.git".format(repo_path)):
            repo = git.Repo.init(repo_path)
        else:
            repo = git.Repo(repo_path)

        repo.git.config('core.sparseCheckout', 'true')

        sparse_checkout_file_path = "{}/.git/info/sparse-checkout".format(repo_path)
        if path:
            with open(sparse_checkout_file_path, "ab+") as scf:
                if path not in scf.readlines():
                    scf.write("{}/{}\n".format(path, name))

        if 'origin' in [remote.name for remote in repo.remotes]:
            origin = repo.remotes['origin']
        else:
            origin = repo.create_remote('origin', (git_repo))

        origin.fetch()
        repo.git.checkout("origin/{}".format(branch))

    def install(self):
        self._update_repositories()
        failed_charts = []
        for chart in self._charts:
            if not self.install_chart(chart, self._charts[chart]):
                logging.error('Helm upgrade failed on {}. Rolling back...'.format(chart))
                self.rollback_chart(chart)
                failed_charts.append(chart)
        if failed_charts:
            logging.error("ERROR: Some charts failed to install and were rolled back")
            for chart in failed_charts:
                logging.error(" - {}".format(chart))

    def rollback_chart(self, release_name):
        list_output = subprocess.check_output(['helm', 'list', '--deployed', release_name])
        if not list_output:
            # Chart has nothing to roll back to
            return
        logging.debug(list_output)
        revision = int(list_output.splitlines()[-1].split('\t')[1].strip())
        args = ['helm', 'rollback', release_name, str(revision)]
        logging.debug(args)
        subprocess.call(args)

    def install_chart(self, release_name, chart):
        chart_name = chart.get('chart', release_name)
        repository_name = self._default_repository

        if chart.get('repository'):
            logging.debug("Repository for {} is {}".format(chart_name, chart.get('repository')))

            if type(chart['repository']) is str:
                repository_name = chart['repository']
                repository_url = None
                repository_git = None
            else:
                repository_name = chart['repository'].get('name')
                repository_url = chart['repository'].get('url')
                repository_git = chart['repository'].get('git')
                repository_path = chart['repository'].get('path', '')

            if repository_git:
                self._fetch_git_chart(chart_name, repository_git, chart.get('version', "master"),  repository_path)
                repository_name = '{}/{}/{}'.format(self._archive, re.sub(r'\:\/\/|\/|\.', '_', repository_git), repository_path)
            elif repository_name not in self.installed_repositories and repository_url:
                self._intall_repository(repository_name, repository_url)

        args = ['helm', 'upgrade', '--install', '{}'.format(release_name), '{}/{}'.format(repository_name, chart_name)]

        if chart.get('version'):
            args.append('--version={}'.format(chart.get('version')))

        if chart.get('files'):
            for file in chart['files']:
                args.append("-f={}".format(file))

        if chart.get('values'):
            for key in chart['values']:
                args.append("--set={}={}".format(key, chart['values'][key]))

        args.append('--namespace={}'.format(chart.get('namespace', self._namespace)))

        logging.debug(' '.join(args))
        args = map(os.path.expandvars, args)
        return not bool(subprocess.call(args))
