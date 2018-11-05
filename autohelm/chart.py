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

from collections import OrderedDict
from string import Template

from exception import AutoHelmCommandException
from config import Config
from repository import Repository
from helm import Helm


default_repository = {'name': 'stable', 'url': 'https://kubernetes-charts.storage.googleapis.com'}


class Chart(object):

    def __init__(self, chart):
        self.helm = Helm()
        self.config = Config()
        self._release_name = chart.keys()[0]
        self._chart = chart[self._release_name]
        self._repository = Repository(self._chart.get('repository', default_repository))
        self._chart['values'] = self.ordereddict_to_dict(self._chart.get('values', {}))
        value_strings = self._chart.get('values-strings', {})
        self._chart['values_strings'] = self.ordereddict_to_dict(value_strings)
        if value_strings != {}:
            del(self._chart['values-strings'])

    @property
    def release_name(self):
        return self._release_name

    @property
    def name(self):
        return self._chart.get('chart', self._release_name)

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

        release = [release for release in self.helm.releases.deployed if release.name == self._release_name][0]
        if release:
            release.rollback()

    def update_dependencies(self):

        if self.config.local_development or self.config.dryrun:
            return True
        logging.debug("Updating chart dependencies: {}".format(self.chart_path))
        if os.path.exists(self.chart_path):
            try:
                r = self.helm.dependency_update(self.chart_path)
            except AutoHelmCommandException, e:
                logging.warn("Unable to update chart dependancies: {}".format(e.stderr))

    def install(self, namespace):

        # Set the namespace
        _namespace = self.namespace or namespace

        self.repository.install(self.name, self.version)            
        self.chart_path = self.repository.chart_path
        # Update the helm dependencies
        self.update_dependencies()

        # Build the args for the chart installation
        # And add any extra arguments
        args = ['--install', '{}'.format(self._release_name), self.chart_path]
        args.extend(self.debug_args)
        args.extend(self.helm_args)

        # Add specific version of chart if set
        if self.version:
            args.append('--version={}'.format(self.version))

        # Build the arguments for values file(s)
        for file in self.files:
            args.append("-f={}".format(file))

        # Build `--set=...` arguments with values set for the chart in the course
        for key, value in self.values.iteritems():
            for k, v in self._format_set(key, value):
                args.append("--set={}={}".format(k, v))

        # Build `--set-string=...` arguments for the chart in the course
        for key, value in self.values_strings.iteritems():
            for k, v in self._format_set(key, value):
                args.append("--set-string={}={}".format(k, v))

        # Append the namespace you'd like to install the chart in
        args.append('--namespace={}'.format(_namespace))

        # Run the pre-install-hook if set
        if self._pre_install_hook:
            logging.debug("Running pre_install hook:")
            self.run_hook(pre_install_hook)

        # Assure all environment variables are set for the chart
        try:
            args = [Template(arg).substitute(os.environ) for arg in args]
        except KeyError, e:
            raise Exception("Missing requirement environment variable: {}".format(e.args[0]))

        # If local_development is not False
        if not self.config.local_development:
            # Try to perform the actual helm install and return error for any
            # failed chart installs
            try:
                r = self.helm.upgrade(*args)
            except AutoHelmCommandException, e:
                logging.error("Failed to upgrade/install {}: {}".format(self.release_name, e.stderr))
                return False

        # If there are any post-install-hooks, run them
        if self._post_install_hook:
            logging.debug("Running post_install hook:")
            self.run_hook(post_install_hook)

        return True
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
        if type(value) == list:
            for index, item in enumerate(value):
                if type(item) == dict:
                    for k, v in self._format_set("{}[{}]".format(key, index), item):
                        yield k, v
                else:
                    yield "{}[{}]".format(key, index), item
        else:
            yield key, value
