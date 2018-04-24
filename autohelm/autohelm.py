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

from collections import OrderedDict
from git import GitCommandError
from string import Template


class AutoHelm(object):

    _default_namespace = 'kube-system'
    _default_repository = 'stable'

    def __init__(self, file=None, dryrun=False, debug=False, charts=None):

        self._home = os.environ.get('HELM_HOME')
        self._dryrun = dryrun
        self._debug = debug

        logging.debug("Checking for local Helm directories.")
        if self._home is None:
            self._home = os.environ.get('HOME') + "/.helm"
            logging.warn("$HELM_HOME not set. Using ~/.helm")

        self._archive = self._home + '/cache/archive'
        if not os.path.isdir(self._archive):
            logging.error("{} does not exist. Have you run `helm init`?".format(self._archive))
            sys.exit()

        logging.debug("Checking for Tiller")
        if not self.tiller_present:
            logging.error("Tiller not present in cluster. Have you run `helm init`?")
            sys.exit()

        plan = yaml.load(file)

        selected_charts = charts or plan.get('charts').iterkeys()
        self._charts = {name: chart for name, chart in plan.get('charts').iteritems() if name in selected_charts}

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
        """ Returns list of installed reposotories """
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
        """ Update repositories """
        args = ['helm', 'repo', 'update']
        logging.debug(" ".join(args))
        subprocess.call(args)

    def _intall_repository(self, name, url):
        """ Install Helm repository """
        args = ['helm', 'repo', 'add', name, url]
        logging.debug(" ".join(args))
        subprocess.call(args)

    def _fetch_git_chart(self, name, git_repo, branch, path):
        """ Does a sparse checkout for a git repository git_repo@branch and retrieves the chart at the path """
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
            logging.debug("Configuring sparse checkout for path: {}".format(path))
        else:
            path = ""

        if 'origin' in [remote.name for remote in repo.remotes]:
            origin = repo.remotes['origin']
        else:
            origin = repo.create_remote('origin', (git_repo))

        origin.fetch()
        repo.git.checkout("origin/{}".format(branch))

        try:
            origin.fetch()
            repo.git.checkout("origin/{}".format(branch))
        except GitCommandError, e:
            logging.error(e)
            if 'Sparse checkout leaves no entry on working directory' in str(e):
                logging.error("Cannot sparse checkout path {} from the chart repository. Remove path when chart exists at the directory root".format(path))
            sys.exit(1)
        except Exception, e:
            raise e
        finally:
            # Remove sparse-checkout to prevent path issues from poisoning the cache
            if os.path.isfile(sparse_checkout_file_path):
                os.remove(sparse_checkout_file_path)

    def run_hook(self, coms):
        """ Expects a list of shell commands. Runs the commands defined by the hook """
        if type(coms) == str:
            coms = [coms]

        for com in coms:
            logging.debug("Running Hook {}".format(com))
            ret = subprocess.call(com, shell=True, executable="/bin/bash")
            if ret != 0:
                logging.error("Hook command `{}` returne non-zero exit code".format(com))
                sys.exit(1)


    def install(self):
        self._update_repositories()
        failed_charts = []
        for chart in self._charts:
            logging.debug("Installing {}".format(chart))
            if not self.install_chart(chart, self._charts[chart]):
                logging.error('Helm upgrade failed on {}. Rolling back...'.format(chart))
                self.rollback_chart(chart)
                failed_charts.append(chart)
            post_install_hook = self._charts[chart].get('hooks', {}).get('post_install')
            if post_install_hook:
                logging.debug("Running post_install hook:")
                self.run_hook(post_install_hook)
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

    def debug_args(self):
        if self._debug:
            return ['--debug']
        if self._dryrun:
            return ['--dry-run', '--debug']
        return []

    def _format_set(self, key, value):
        """Allows nested yaml to be set on the command line of helm. 
        Accepts key and value, if value is an ordered dict, recussively
        formats the string properly """
        logging.debug("Key: {}".format(key))
        logging.debug("Value: {}".format(value))

        if type(value) == OrderedDict:            
            for new_key, new_value in value.iteritems():
                return self._format_set("{}.{}".format(key, new_key), new_value)
        else:
            return key, value

    def ensure_repository(self, release_name, chart_name, repository, version):
        repository_name = self._default_repository
        if repository:
            logging.debug("Repository for {} is {}".format(chart_name, repository))

            if type(repository) is str:
                repository_name = repository
                repository_url = None
                repository_git = None
            else:
                repository_name = repository.get('name')
                repository_url = repository.get('url')
                repository_git = repository.get('git')
                repository_path = repository.get('path', '')

            if repository_git:
                self._fetch_git_chart(chart_name, repository_git, version,  repository_path)
                repository_name = '{}/{}/{}'.format(self._archive, re.sub(r'\:\/\/|\/|\.', '_', repository_git), repository_path)
            elif repository_name not in self.installed_repositories and repository_url:
                self._intall_repository(repository_name, repository_url)
        return repository_name

    def install_chart(self, release_name, chart):
        chart_name = chart.get('chart', release_name)

        repository_name = self.ensure_repository(release_name, chart_name, chart.get('repository'), chart.get('version', "master"))

        args = ['helm', 'upgrade', '--install', '{}'.format(release_name), '{}/{}'.format(repository_name, chart_name)]
        args.extend(self.debug_args())

        if chart.get('version'):
            args.append('--version={}'.format(chart.get('version')))

        for file in chart.get('files', []):
            args.append("-f={}".format(file))

        for key, value in chart.get('values', {}).iteritems():
            k, v = self._format_set(key, value)
            args.append("--set={}={}".format(k, v))
        for key, value in chart.get('values-strings', {}).iteritems():
            k, v = self._format_set(key, value)
            args.append("--set-string={}={}".format(k, v))

        args.append('--namespace={}'.format(chart.get('namespace', self._namespace)))

        logging.debug(' '.join(args))

        pre_install_hook = chart.get("hooks", {}).get('pre_install')
        if pre_install_hook:
            logging.debug("Running pre_install hook:")
            self.run_hook(pre_install_hook)

        try:
            args = [Template(arg).substitute(os.environ) for arg in args]
        except KeyError, e:
            raise Exception("Missing requirement environment variable: {}".format(e.args[0]))
        return not bool(subprocess.call(args))
