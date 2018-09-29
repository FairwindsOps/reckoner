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

import logging
import subprocess
import git
import os
import sys
import re
import semver
import json

from collections import OrderedDict
from git import GitCommandError
from string import Template
from meta import __version__ as autohelm_meta_version

# from . import AutoHelmSubprocess as subprocess

class AutohelmException(Exception):
    pass

class Core(object):
    _installed_repositories = []
    _home = None

    def __init__(self):
        logging.debug("Checking for local Helm directories.")
        if self._home is None:
            self._home = os.environ.get('HOME') + "/.helm"
            logging.warn("$HELM_HOME not set. Using ~/.helm")

        self._archive = self._home + '/cache/archive'
        if not os.path.isdir(self._archive):
            logging.critical("{} does not exist. Have you run `helm init`?".format(self._archive))
            sys.exit(1)

    @property
    def installed_repositories(self):

        if self._installed_repositories != []:
            return self._installed_repositories

        args = ['helm', 'repo', 'list']

        for repo in [line.split() for line in subprocess.check_output(args).split('\n')[1:-1]]:
            self._installed_repositories.append({'name': repo[0], 'url': repo[1]})
        logging.debug("Getting installed repositories: {}".format(self._installed_repositories))
        return self._installed_repositories


class Repository(Core):

    def __init__(self, repository):
        super(Repository, self).__init__()
        logging.debug("Repository: {}".format(repository))
        self._repository = {}
        if type(repository) is str:
            self._repository['name'] = repository
        else:
            self._repository['name'] = repository.get('name')
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
        logging.debug("Installing Chart Repository: {}".format(self.name))
        if self.git is None:
            if self._repository not in self.installed_repositories:
                args = ['helm', 'repo', 'add', self.name, self.url]
                logging.debug(" ".join(args))
                subprocess.call(args)
            else:
                logging.debug("Chart repository {} already installed".format(self.name))


class Chart(Core):

    def __init__(self, chart, namespace="kube_system", repository="stable"):
        super(Chart, self).__init__()
        logging.debug(chart)
        self._release_name = chart.keys()[0]
        self._chart = chart[self._release_name]
        self._namespace = self.namespace or namespace
        self._repository = Repository(self._chart.get('repository', repository))

    @property
    def name(self):
        return self._chart.get('chart', self._release_name)

    @property
    def values(self):
        return dict(self._chart.get('values', {}))

    @property
    def values_strings(self):
        return dict(self._chart.get('values-strings', {}))

    @property
    def files(self):
        return dict(self._chart.get('files', []))

    @property
    def namespace(self):
        return self._namespace

    @property
    def repository(self):
        return self._repository

    def __getattr__(self, key):
        return self._chart.get(key)

    def __str__(self):
        return str(dict(self._chart))

    def run_hook(self, coms):
        """ Expects a list of shell commands. Runs the commands defined by the hook """
        if type(coms) == str:
            coms = [coms]

        for com in coms:
            logging.debug("Running Hook {}".format(com))
            ret = subprocess.call(com, shell=True, executable="/bin/bash")
            if ret != 0:
                logging.error("Hook command `{}` returned non-zero exit code".format(com))
                sys.exit(1)

    def rollback(self):
        list_output = subprocess.check_output(['helm', 'list', '--deployed', self._release_name])
        if not list_output:
            # Chart has nothing to roll back to
            return
        logging.debug(list_output)
        revision = int(list_output.splitlines()[-1].split('\t')[1].strip())
        args = ['helm', 'rollback', self._release_name, str(revision)]
        logging.debug(args)
        if not self._dryrun:
            subprocess.call(args)

    def install(self, debug=False, dryrun=False):
        self._debug = debug
        self._dryrun = dryrun

        if self.repository.git:
            self.repository.name = '{}/{}/{}'.format(self._archive, re.sub(r'\:\/\/|\/|\.', '_', self.repository.git), self.repository.path)
            self._fetch_from_git_repository(self.repository.name, self.repository.git, self.version, self.repository.path)
        else:
            self.repository.install()

        chart_path = '{}/{}'.format(self.repository.name, self.name)
        args = ['helm', 'dependency', 'update', chart_path]
        logging.debug("Updating chart dependencies: {}".format(chart_path))
        logging.debug(" ".join(args))
        subprocess.call(args)

        args = ['helm', 'upgrade', '--install', '{}'.format(self._release_name), chart_path]
        args.extend(self.debug_args())

        if self.version:
            args.append('--version={}'.format(self.version))

        for file in self.files:
            args.append("-f={}".format(file))

        for key, value in self.values.iteritems():
            for k, v in self._format_set(key, value):
                args.append("--set={}={}".format(k, v))
        for key, value in self.values_strings.iteritems():
            for k, v in self._format_set(key, value):
                args.append("--set-string={}={}".format(k, v))

        args.append('--namespace={}'.format(self.namespace))

        logging.debug(' '.join(args))

        if self._pre_install_hook:
            logging.debug("Running pre_install hook:")
            self.run_hook(pre_install_hook)

        try:
            args = [Template(arg).substitute(os.environ) for arg in args]
        except KeyError, e:
            raise Exception("Missing requirement environment variable: {}".format(e.args[0]))
        if not self._local_development:
            return not bool(subprocess.call(args))

        if self._post_install_hook:
            logging.debug("Running post_install hook:")
            self.run_hook(post_install_hook)
        return True

    # # If the chart_name is in the repo path and appears to be redundant pb
    # if self.name.endswith(self.name) and os.path.isdir(self.repository) and not os.path.isdir('{}/{}'.format(repository_name, self.name)):
    #     logging.warn("Chart name {} in {}. Removing to try and prevent errros.".format(chart_name, repository_name))
    #     repository_name = repository_name[:-len(chart_name) - 1]

    def _fetch_from_git_repository(self, name, git_repo, branch, path):
        """ Does a sparse checkout for a git repository git_repo@branch and retrieves the chart at the path """

        def fetch_pull(ref):
            """ Do the fetch, checkout pull for the git ref """
            origin.fetch(tags=True)
            repo.git.checkout("{}".format(ref))
            repo.git.pull("origin", "{}".format(ref))

        repo_path = '{}/{}'.format(self._archive, re.sub(r'\:\/\/|\/|\.', '_', self.repository.git))
        if not os.path.isdir(repo_path):
            os.mkdir(repo_path)

        if not os.path.isdir("{}/.git".format(repo_path)):
            repo = git.Repo.init(repo_path)
        else:
            repo = git.Repo(repo_path)

        sparse_checkout_file_path = "{}/.git/info/sparse-checkout".format(repo_path)
        if self.path not in ['', '/', './']:
            repo.git.config('core.sparseCheckout', 'true')
            if self.path:
                with open(sparse_checkout_file_path, "ab+") as scf:
                    if path not in scf.readlines():
                        scf.write("{}/{}\n".format(self.path, self.name))
                logging.debug("Configuring sparse checkout for path: {}".format(self.path))
        else:
            logging.warn("Ignoring path argument \"{}\"! Remove path when chart exists at the repository root".format(path))

        if 'origin' in [remote.name for remote in repo.remotes]:
            origin = repo.remotes['origin']
        else:
            origin = repo.create_remote('origin', (self.git))

        try:
            chart_path = "{}/{}/{}".format(repo_path, self.path, self._chart_name)
            fetch_pull(self.version)
        except GitCommandError, e:
            if 'Sparse checkout leaves no entry on working directory' in str(e):
                logging.warn("Error with path \"{}\"! Remove path when chart exists at the repository root".format(path))
                logging.warn("Skipping chart {}".format(self._chart_name))
                return False
            elif 'did not match any file(s) known to git.' in str(e):
                logging.warn("Branch/tag \"{}\" does not seem to exist!".format(self.version))
                logging.warn("Skipping chart {}".format(self._chart_name))
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

    def debug_args(self):
        if self._dryrun:
            return ['--dry-run', '--debug']
        if self._debug:
            return ['--debug']
        return []

    def _format_set(self, key, value):
        """Allows nested yaml to be set on the command line of helm.
        Accepts key and value, if value is an ordered dict, recussively
        formats the string properly """

        if type(value) == OrderedDict:
            for new_key, new_value in value.iteritems():
                for k, v in self._format_set("{}.{}".format(key, new_key), new_value):
                    for a, b in self._format_set_list(k, v):
                        yield a, b
        else:
            for a, b in self._format_set_list(key, value):
                yield a, b

    def _format_set_list(self, key, value):
        """ given a list and a key, format it properly for the helm set list indexing """
        logging.debug("Key: {}".format(key))
        logging.debug("Value: {}".format(value))
        if type(value) == list:
            for index, item in enumerate(value):
                if type(item) == OrderedDict:
                    logging.debug("Item: {}".format(item))
                    for k, v in self._format_set("{}[{}]".format(key, index), item):
                        yield k, v
                else:
                    yield "{}[{}]".format(key, index), item
        else:
            yield key, value


class Course(Core):

    def __init__(self, file):
        super(Course, self).__init__()
        self._dict = yaml.load(file)
        self._repositories = []
        for name, repository in self._dict.get('repositories', {}).iteritems():
            repository['name'] = name
            self._repositories.append(Repository(repository))

    def __str__(self):
        return str(self._dict)

    @property
    def repositories(self):
        return self._repositories

    def __getattr__(self, key):
        return self._dict.get(key)


class AutoHelm(Core):

    def __init__(self, file=None, dryrun=False, debug=False, charts=None, helm_args=None, local_development=False):

        super(AutoHelm, self).__init__()

        self._dryrun = dryrun
        self._debug = debug
        self._helm_args = helm_args
        self._local_development = local_development
        if self._local_development:
            logging.info("Local Development is ON")

        self._course = Course(file)
        self._selected_charts = charts or self._course.charts.iterkeys()
        self._load_charts()

        if not self._local_development:
            logging.debug("Checking for correct cluster context")
            self._context = self._course.context or self.current_context
            self._update_context()

            logging.debug("Checking for Tiller")
            if not self.tiller_present:
                logging.error("Tiller not present in cluster. Have you run `helm init`?")
                sys.exit(1)

            for repo in self._course.repositories:
                repo.install()

    def _load_charts(self):
        _charts = []
        defaults = {
            "namespace": self._course.namespace,
        }

        for name, chart in self._course.charts.iteritems():
            if name in self._selected_charts:
                _charts.append(Chart({name: chart}, **defaults))

        self._charts = _charts

    def install(self):
        self._compare_required_versions()
        self._update_repositories()
        failed_charts = []
        for chart in self._charts:
            logging.debug("Installing {}".format(chart.name))

            if not chart.install(self._debug, self._dryrun):
                logging.error('Helm upgrade failed on {}. Rolling back...'.format(chart))
                chart.rollback
                failed_charts.append(chart)

        if failed_charts:
            logging.error("ERROR: Some charts failed to install and were rolled back")
            for chart in failed_charts:
                logging.error(" - {}".format(chart))
            sys.exit(1)

    @property
    def current_context(self):
        """ Returns the current cluster context """
        args = ['kubectl', 'config', 'current-context']
        resp = subprocess.check_output(args)
        self._current_context = resp.strip()
        return self._current_context

    @property
    def helm_version(self):
        """ return version of installed helm binary """
        args = ['helm', 'version', '--client']
        resp = subprocess.check_output(args)
        _helm_version = resp.replace('Client: &version.Version', '').split(',')[0].split(':')[1].replace('v', '').replace('"', '')
        return _helm_version

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

    def _set_context(self, context):
        """ Set the cluster context """
        args = ['kubectl', 'config', 'use-context', context]
        logging.debug(" ".join(args))
        subprocess.call(args)

    def _update_context(self):
        """ Update the current context to the desired context """
        logging.debug("Current cluster context is: {}".format(self.current_context))
        if self.current_context != self._context:
            logging.debug("Updating cluster context to {}".format(self._context))
            self._set_context(self._context)

        if self.current_context == self._context:
            return True
        else:
            raise AutoHelmException("Unable to set cluster context to: {}".format(self._context))

    def _compare_required_versions(self):
        """ Compare installed versions of helm and autohelm to the minimum versions required by the course.yml """
        if self._course.minimum_versions is None:
            return True
        helm_mv = self._course.minimum_versions.get('helm', '0.0.0')
        autohelm_mv = self._course.minimum_versions.get('autohelm', '0.0.0')

        logging.debug("Helm Minimum Version is: {}".format(helm_mv))
        helm_version = self.helm_version
        logging.debug("Helm Installed Version is {}".format(helm_version))

        logging.debug("Autohelm Minimum Version is {}".format(autohelm_mv))
        autohelm_version = autohelm_meta_version
        logging.debug("Autohelm Installed Version is {}".format(autohelm_version))

        r1 = semver.compare(autohelm_version, autohelm_mv)
        if r1 < 0:
            raise AutohelmException("autohelm Minimum Version {} not met.".format(autohelm_mv))
        r2 = semver.compare(helm_version, helm_mv)
        if r2 < 0:
            raise AutohelmException("helm Minimum Version {} not met.".format(helm_mv))

        return True

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

            if repository_git and not self._local_development:
                repository_name = '{}/{}/{}'.format(self._archive, re.sub(r'\:\/\/|\/|\.', '_', repository_git), repository_path)
                if self._fetch_git_chart(chart_name, repository_git, version,  repository_path) is False:
                    return False
            elif repository_name not in self.installed_repositories and repository_url:
                self._install_repository(repository_name, repository_url)
        return repository_name

    def install_chart(self, release_name, chart):
        chart_name = chart.get('chart', release_name)
        repository_name = self.ensure_repository(release_name, chart_name, chart.get('repository'), chart.get('version', "master"))
        if repository_name is False:
            logging.error("Unable to install chart: {}".format(chart_name))
            return False

        # If the chart_name is in the repo path and appears to be redundant pb
        if repository_name.endswith(chart_name) and os.path.isdir(repository_name) and not os.path.isdir('{}/{}'.format(repository_name, chart_name)):
            logging.warn("Chart name {} in {}. Removing to try and prevent errros.".format(chart_name,repository_name))
            repository_name = repository_name[:-len(chart_name)-1]

        chart_path = '{}/{}'.format(repository_name, chart_name)
        args = ['helm', 'dependency', 'update', chart_path]
        logging.debug("Updating chart dependencies: {}".format(chart_path))
        logging.debug(" ".join(args))
        subprocess.call(args)

        args = ['helm', 'upgrade', '--install', '{}'.format(release_name), chart_path]
        args.extend(self.debug_args())

        if chart.get('version'):
            args.append('--version={}'.format(chart.get('version')))

        for file in chart.get('files', []):
            args.append("-f={}".format(file))

        for key, value in chart.get('values', {}).iteritems():
            for k, v in self._format_set(key, value):
                args.append("--set={}={}".format(k, v))
        for key, value in chart.get('values-strings', {}).iteritems():
            for k, v in self._format_set(key, value):
                args.append("--set-string={}={}".format(k, v))

        for helm_arg in self._helm_args:
            args.append("{}".format(helm_arg))

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
        if not self._local_development:
            return not bool(subprocess.call(args))

        return True
