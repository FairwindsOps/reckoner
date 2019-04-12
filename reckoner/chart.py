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

import logging
import os

from collections import OrderedDict
from string import Template

from .exception import ReckonerCommandException
from .config import Config
from .repository import Repository
from .helm.client import HelmClientException
from .command_line_caller import call

default_repository = {'name': 'stable', 'url': 'https://kubernetes-charts.storage.googleapis.com'}


class Chart(object):
    """
    Description:
    - Chart class for each release in the course.yml

    Arguments:
    - chart (dict):
    - helm: Instance of HelmClient()

    Attributes:
    - config: Instance of Config()
    - release_name : String. Name of the release
    - name: String. Name of chart
    - files: List. Values files
    - namespace

    Returns:
    - Instance of Response() is truthy where Response.exitcode == 0
    - Instance of Response() is falsey where Response.exitcode != 0
    """

    def __init__(self, chart, helm):
        self.helm = helm
        self.config = Config()
        self._release_name = list(chart.keys())[0]
        self._chart = chart[self._release_name]
        self._repository = Repository(self._chart.get('repository', default_repository), self.helm)
        self._chart['values'] = self._chart.get('values', {})
        self._chart['set_values'] = self._chart.get('set-values', {})

        self._namespace = self._chart.get('namespace')
        self._context = self._chart.get('context')
        value_strings = self._chart.get('values-strings', {})
        self._chart['values_strings'] = value_strings

        if value_strings != {}:
            del(self._chart['values-strings'])

        self._deprecation_messages = []

    @property
    def helm_args(self):
        """ Returns list of extra options/args for the helm command """
        if self.config.helm_args is not None:
            return self.config.helm_args
        return []

    @property
    def release_name(self):
        """
        Returns release name of course chart
        """
        return self._release_name

    @property
    def name(self):
        """
        Returns chart name of course chart
        """
        return self._chart.get('chart', self._release_name)

    @property
    def debug_args(self):
        """ Returns list of Helm debug arguments """

        if self.config.dryrun:
            return ['--dry-run', '--debug']
        if self.config.debug:
            return ['--debug']

        return []

    @property
    def files(self):
        """ List of values files from the course chart """
        logging.debug(self)
        return list(self._chart.get('files', []))

    @property
    def namespace(self):
        """ Namespace to install the course chart """
        return self._namespace

    @property
    def context(self):
        """ Namespace to install the course chart """
        return self._context

    @property
    def repository(self):
        """ Repository object parsed from course chart """
        return self._repository

    def pre_install_hook(self):
        self.run_hook('pre_install')

    def post_install_hook(self):
        self.run_hook('post_install')

    def run_hook(self, hook_type):
        """ Hook Type. Runs the commands defined by the hook """
        commands = self._get_hook(hook_type)
        if commands is None:
            return commands
        if type(commands) == str:
            commands = [commands]

        for command in commands:
            if self.config.local_development or self.config.dryrun:
                logging.warning("Hook not run due to --dry-run: {}".format(command))
                continue
            else:
                logging.info("Running {} hook...".format(hook_type))

            try:
                result = call(
                    command,
                    shell=True,
                    executable="/bin/bash",
                    path=self.config.course_base_directory
                )
            except Exception as error:
                # NOTE This block is only used when we cannot send the call or
                #      have other unexpected errors running the command.
                #      The call()->Response should pass a Response object back
                #      even when the exit code != 0.
                logging.error("Critical Error running the command hook.")
                logging.error(error)
                raise ReckonerCommandException(
                    "Uncaught exception while running hook "
                    "'{}'".format(command)
                )

            command_successful = result.exitcode == 0

            logging.info("Ran Hook: '{}'".format(result.command_string))
            _output_level = logging.INFO  # The level to log the command output

            if command_successful:
                logging.info("{} hook ran successfully".format(hook_type))
            else:
                logging.error("{} hook failed to run".format(hook_type))
                logging.error("Returned exit code: {}".format(result.exitcode))
                # Override message level response to bubble up error visibility
                _output_level = logging.ERROR

            # only print stdout if there is content
            if result.stdout:
                logging.log(_output_level,
                            "Returned stdout: {}".format(result.stdout))
            # only print stderr if there is content
            if result.stderr:
                logging.log(_output_level,
                            "Returned stderr: {}".format(result.stderr))

            # Always raise an error after failures
            if not command_successful:
                raise ReckonerCommandException(
                    "Hook ({}) failed to run".format(result.command_string),
                    stdout=result.stdout,
                    stderr=result.stderr,
                )

    def rollback(self):
        """ Rollsback most recent release of the course chart """
        release = [release for release in self.helm.releases.deployed if release.name == self._release_name][0]
        if release:
            release.rollback()

    def update_dependencies(self):
        """ Update the course chart dependencies """
        if self.config.local_development or self.config.dryrun:
            return True
        logging.debug("Updating chart dependencies: {}".format(self.repository.chart_path))
        if os.path.exists(self.repository.chart_path):
            try:
                response = self.helm.dependency_update(self.repository.chart_path)
                logging.debug(response.stderr + "\n" + response.stdout)
            except ReckonerCommandException as error:
                logging.warn("Unable to update chart dependencies: {}".format(error.stderr))

    def install(self, namespace=None, context=None):
        """
        Description:
        - Upgrade --install the course chart

        Arguments:
        - namespace (string). Passed in but will be overridden by Chart().namespace if set
        """

        # Set the namespace
        if self.namespace is None:
            self._namespace = namespace

        # Set the context
        if self.context is None:
            self._context = context

        # Fire the pre_install_hook
        self.pre_install_hook()

        # TODO: Improve error handling of a repository installation
        #       Thoughts here, perhaps it would be better to install the
        #       repositories *before* trying to install the chart. This
        #       way we could find out earlier our course is wrong.
        self.repository.install(self.name, self.version)

        # Update the helm dependencies
        self.update_dependencies()

        # Build the args for the chart installation
        # And add any extra arguments
        self.build_helm_arguments_for_chart()

        # Check and Error if we're missing required env vars
        self._check_env_vars()

        # Perform the upgrade with the arguments
        try:
            # Try to run helm upgrade
            helm_command_response = self.helm.upgrade(self.args)
            # Log the stdout response in info
            logging.info(helm_command_response.stdout)
        except HelmClientException as error:
            logging.error(error)
            return

        # Fire the post_install_hook
        self.post_install_hook()

        if self._deprecation_messages:
            [logging.warning(msg) for msg in self._deprecation_messages]

    def build_helm_arguments_for_chart(self):
        """
        This method builds all the arguments we'll pass along to the helm
        client once we need to run the install
        """

        # Set Default args (release name and chart path)
        self.args = [
            '{}'.format(self._release_name),
            self.repository.chart_path,
        ]

        # Add namespace to args
        self.args.append('--namespace={}'.format(self.namespace))

        # Add kubecfg context
        if self.context is not None:
            self.args.append('--kube-context={}'.format(self.context))

        # Add debug arguments
        self.args.extend(self.debug_args)

        # Add the version arguments
        if self.version:
            self.args.append('--version={}'.format(self.version))

        # HACK: This is in place until we can fully deprecate the usage of set
        #       in place of values. Currently values: gets translated into
        #       --set commands to the helm command line run. This should be
        #       changed so that set: goes to command line args and values: goes
        #       to temporary values files, to keep strong types in yaml.
        #       This will go away once we fully change the functionality of
        #       values: vs sets: settings in course.yml
        self._merge_set_and_values()

        # Build the list of existing yaml files to use for the helm command
        self.build_files_list()

        # Build the file arguments from the `values: {}` in course.yml
        self.build_temp_values_files()

        # Build the list of --set arguments
        self.build_set_arguments()

        # Build the list of --set-string arguments
        self.build_set_string_arguments()

    def build_temp_values_files(self):
        """
        This method builds temporary files based on the values: settings
        provided in the course.yml. This effectively keeps type persistence
        between the course.yml and what is passed to helm. If you use set:
        value arguments then you can lose types like int, float and true/false
        """
        if self.values:
            self._deprecation_messages.append(
                "DEPRECATION NOTICE: Change 'values: {}' to 'set-values: {}' "
                "to keep consistent behavior beyond v1.1+. Details: "
                "https://github.com/reactiveops/reckoner/issues/7"
            )

    def build_files_list(self):
        """
        This method builds the files list for all
        files specified in the course.yml
        """
        for values_file in self.files:
            self.args.append("-f={}".format(values_file))

    def build_set_string_arguments(self):
        """
        Builder for "set-string" arguments in helm command line
        This method specifically modifies the Chart object to
        prepare the command line arguments.

        Note running this multiple times will provide duplicate arguments
        """
        for key, value in self.values_strings.items():
            for k, v in self._format_set(key, value):
                self.args.append("--set-string={}={}".format(k, v))

    def build_set_arguments(self):
        """
        Builder for "set" arguments in helm command line
        This method specifically modifies the Chart object to
        prepare the command line arguments.

        Note running this multiple times will provide duplicate arguments
        """
        for key, value in self.set_values.items():
            for k, v in self._format_set(key, value):
                self.args.append("--set={}={}".format(k, v))

    def _format_set(self, key, value):
        """
        Allows nested yaml to be set on the command line of helm.
        Accepts key and value, if value is an ordered dict, recursively
        formats the string properly
        """
        if type(value) in [dict, OrderedDict]:
            for new_key, new_value in value.items():
                for k, v in self._format_set("{}.{}".format(key, new_key), new_value):
                    for a, b in self._format_set_list(k, v):
                        yield a, b
        else:
            for a, b in self._format_set_list(key, value):
                yield a, b

    def _format_set_list(self, key, value):
        """
        given a list and a key, format it properly
        for the helm set list indexing
        """
        if type(value) == list:
            for index, item in enumerate(value):
                if type(item) in [dict, OrderedDict]:
                    for k, v in self._format_set("{}[{}]".format(key, index), item):
                        yield k, v
                else:
                    yield "{}[{}]".format(key, index), item
        else:
            yield key, value

    def __getattr__(self, key):
        return self._chart.get(key)

    def _merge_set_and_values(self):
        """
        This is a temporary method that will be gone once the values: vs set:
        debacle has been resolved. (See https://github.com/reactiveops/reckoner/issues/7)

        NOTE ONLY RUN THIS ONCE BECAUSE IT'S NOT IDEMPOTENT
        """
        if self._hack_set_values_already_merged:
            raise Exception('This method cannot be called twice. '
                            'If you are seeing this please open an '
                            'issue in github.')

        def merge_dicts(values, sets):
            """This does a dict merge and prefers "sets" values"""
            new_dict = values.copy()
            new_dict.update(sets)
            return new_dict

        logging.debug('Merging values: into sets: - sets: take precedence.')
        logging.debug('Original value of sets: {}'.format(self.set_values))
        self.set_values = merge_dicts(self.values, self.set_values)
        logging.debug('New value of sets: {}'.format(self.set_values))
        self._hack_set_values_already_merged = True

    def __str__(self):
        return str(dict(self._chart))

    def _get_hook(self, hook_type):
        if self.hooks is not None:
            return self.hooks.get(hook_type)

    def _check_env_vars(self):
        """
        accepts list of args
        if any of those appear to be env vars
        and are missing from the environment
        an exception is raised
        """
        for idx in range(len(self.args)):
            try:
                self.args[idx] = Template(self.args[idx]).substitute(os.environ)
            except ValueError:
                logging.debug("Could not replace Variable {} with an Env Var: Formatting Error.".format(self.args[idx]))
                logging.debug("This generally happens if you use $(THING) instead of $THING or ${THING}.")
                continue
            except KeyError:
                raise Exception("Missing requirement environment variable: {}".format(self.args[idx]))
