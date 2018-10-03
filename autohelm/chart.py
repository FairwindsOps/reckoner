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
import subprocess
import os
import re
import git

from collections import OrderedDict
from string import Template

from . import call
from exception import AutoHelmCommandException
from config import Config
from repository import Repository


default_repository = {'name': 'stable', 'url': 'https://kubernetes-charts.storage.googleapis.com'}

class Chart(object):

    def __init__(self, chart):
        self.config = Config()
        logging.debug(chart)
        self._release_name = chart.keys()[0]
        self._chart = chart[self._release_name]
        self._repository = Repository(self._chart.get('repository', default_repository))

    @property
    def release_name(self):
        return self._release_name

    @property
    def name(self):
        return self._chart.get('chart', self._release_name)

    @property
    def values(self):
        if self._values == None:
            self._values = self.ordereddict_to_dict(self._chart.get('values', {}))

        return self._values

    def ordereddict_to_dict(self, value):
        for k, v in value.items():
            if type(v) == OrderedDict:
                value[k] = self.ordereddict_to_dict(v)
            if type(v) == list:
                for item in v:
                    if type(item) == OrderedDict:
                        v.remove(item)
                        v.append(self.ordereddict_to_dict(item))
        return dict(value)

    @property
    def values_strings(self):
        if self._values_strings is None:
            self._values_strings = self.ordereddict_to_dict(self._chart.get('values-strings', {}))
        return self._values_strings

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
        list_output = subprocess.check_output()
        args = ['helm', 'list', '--deployed', self._release_name]
        stdout, stderr, retcode = call(args)
        if stdout:          
            revision = int(stdout.splitlines()[-1].split('\t')[1].strip())
            args = ['helm', 'rollback', self._release_name, str(revision)]
            if not self.config.dryrun and not self.config.local_development:
                call(args)
        return True

    def update_dependencies(self):

        if self.config.local_development or self.config.dryrun:
            return True
        args = ['helm', 'dependency', 'update', self.chart_path]
        logging.debug("Updating chart dependencies: {}".format(self.chart_path))
        try:
            call(args)
        except AutoHelmCommandException, e:
            logging.warn("Unable to update chart dependancies: {}".format(e.stderr) )
    
    def install(self, namespace):

        _namespace = self.namespace or namespace

        if self.repository.git:
            self.repository.name = '{}/{}/{}'.format(self.config.archive, re.sub(r'\:\/\/|\/|\.', '_', self.repository.git), self.repository.path)
            self._fetch_from_git_repository(self.repository.name, self.repository.git, self.version, self.repository.path)
        else:
            self.repository.install()

        self.chart_path = '{}/{}'.format(self.repository.name, self.name)

        self.update_dependencies()

        args = ['helm', 'upgrade', '--install', '{}'.format(self._release_name), self.chart_path]
        args.extend(self.debug_args)
        args.extend(self.helm_args)

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

        args.append('--namespace={}'.format(_namespace))

        if self._pre_install_hook:
            logging.debug("Running pre_install hook:")
            self.run_hook(pre_install_hook)

        try:
            args = [Template(arg).substitute(os.environ) for arg in args]
        except KeyError, e:
            raise Exception("Missing requirement environment variable: {}".format(e.args[0]))
        if not self.config.local_development:
            try:
                stdout, stderr, retcode = call(args)
            except AutoHelmCommandException, e:
                logging.error("Failed to upgrade/install {}: {}".format(self.release_name, e.stderr))
                return False
           

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

        repo_path = '{}/{}'.format(self.config.archive, re.sub(r'\:\/\/|\/|\.', '_', self.repository.git))

        logging.debug('Chart repository path: {}'.format(repo_path))
        if not os.path.isdir(repo_path):
            os.makedirs(repo_path)

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

        if not self.config.local_development:
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

    @property
    def debug_args(self):
        if self.config.dryrun:
            return ['--dry-run', '--debug']
        if self.config.debug:
            return ['--debug']
        return []

    @property
    def helm_args(self):
        if self.config.helm_args is not None:
            return self.config.helm_args
        return []
    

    def _format_set(self, key, value):
        """Allows nested yaml to be set on the command line of helm.
        Accepts key and value, if value is an ordered dict, recursively
        formats the string properly """
        if type(value) == dict:
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
                if type(item) == dict:
                    logging.debug("Item: {}".format(item))
                    for k, v in self._format_set("{}[{}]".format(key, index), item):
                        yield k, v
                else:
                    yield "{}[{}]".format(key, index), item
        else:
            yield key, value

