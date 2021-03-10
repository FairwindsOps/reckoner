# -- coding: utf-8 --

# Copyright 2019 FairwindsOps Inc
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
import re
import difflib
import logging
import traceback

from .hooks import Hook
from .config import Config
from .repository import Repository
from .kube import NamespaceManager
from .exception import ReckonerCommandException, ReckonerException
from .yaml.handler import Handler as yaml_handler
from .manifests import diff as manifestDiff

from .helm.cmd_response import HelmCmdResponse
from .helm.client import HelmClientException
from string import Template
from tempfile import NamedTemporaryFile as tempfile


class ChartResult:

    def __init__(self, name: str, failed: bool, error_reason: str, response: HelmCmdResponse):
        self.name = name
        self.failed = failed
        self.error_reason = error_reason
        self.response = response

    def __str__(self):
        return "Chart Name: {}\n" \
            "Status: {}\n" \
            "Error Reason: {}".format(self.name, self.status_string, self.error_reason)

    @property
    def status_string(self) -> str:
        if self.failed:
            return "Failed"
        else:
            return "Succeeded"


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
    - Instance of Response() is falsy where Response.exitcode != 0
    """

    def __init__(self, chart, helm):
        self._deprecation_messages = []
        self.helm = helm
        self.config = Config()
        self._release_name = list(chart.keys())[0]
        self.result = ChartResult(
            name=self._release_name,
            failed=False,
            error_reason="",
            response=None
        )
        self._chart = chart[self._release_name]
        self._repository = Repository(self._chart.get('repository', {}), self.helm)
        self._plugin = self._chart.get('plugin')
        self._chart['values'] = self._chart.get('values', {})
        self._temp_values_file_paths = []

        self.args = []

        # Parsing and prepping hooks from chart
        self._hooks = self._chart.get('hooks', {})
        self._pre_install_hook = Hook(
            self.hooks.get(
                'pre_install',
                []
            ),
            'Release {} pre install'.format(self.name),
            self.config.course_base_directory
        )

        self._post_install_hook = Hook(
            self.hooks.get(
                'post_install',
                []
            ),
            'Release {} post install'.format(self.name),
            self.config.course_base_directory
        )

        self._namespace = self._interpolate_env_vars_from_string(self._chart.get('namespace', ''))
        self._namespace_management = self._chart.get('namespace_management')
        self._context = self._chart.get('context')

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
    def namespace_management(self):
        """ Namespace to install the course chart """
        return self._namespace_management

    @property
    def context(self):
        """ Namespace to install the course chart """
        return self._context

    @property
    def repository(self):
        """ Repository object parsed from course chart """
        return self._repository

    @property
    def plugin(self):
        """ Helm plugin name parsed from course chart """
        return self._plugin

    @property
    def hooks(self):
        return self._hooks

    @property
    def pre_install_hook(self):
        return self._pre_install_hook

    @property
    def post_install_hook(self):
        return self._post_install_hook

    def rollback(self):
        """ Rollsback most recent release of the course chart """
        release = [release for release in self.helm.releases.deployed if release.name == self._release_name][0]
        if release:
            release.rollback()

    def update_dependencies(self):
        """ Update the course chart dependencies """
        if self.config.dryrun:
            return True

        chart_path = os.path.abspath(
            os.path.join(
                self.config.course_base_directory,
                self.repository.chart_path
            )
        )

        # Is it a chart, is it local
        if os.path.exists(os.path.join(chart_path,"Chart.yaml")):
            logging.info(f"Updating chart dependencies: {self.repository.chart_path}")
            response = self.helm.dependency_update(chart_path)
            logging.debug(response.command)
            logging.debug(response.stdout)
            logging.debug(response.stderr)
            if response.exit_code != 0:
                raise Exception(f'Dependency update failed with "{response.stderr}"')

    def manage_namespace(self):
        """ Creates the charts specified namespace if it does not already exist
        Requires `self.config.create_namespace` to true. Caches the existing namespace list
        in the self.config option to avoid going back to the api for each chart.
        """
        if self.config.create_namespace and not self.dryrun:
            nsm = NamespaceManager(self.namespace, self.namespace_management)
            nsm.create_and_manage()

    def __pre_command(self, default_namespace=None, default_namespace_management={}, context=None) -> None:
        # Set the namespace
        if self.namespace == '':
            self._namespace = default_namespace

        # Set the namespace-management settings
        if self.namespace_management is None:
            self._namespace_management = default_namespace_management

        # Set the context
        if self.context is None:
            self._context = context

        self.repository.install(self.name, self.version)

        # Update the helm dependencies
        self.update_dependencies()

        # Build the args for the chart installation
        # And add any extra arguments
        self.build_helm_arguments_for_chart()

        # Check and Error if we're missing required env vars
        self._check_env_vars()

    def install(self, default_namespace=None, default_namespace_management={}, context=None) -> None:
        """
        Description:
        - Upgrade --install the course chart

        Arguments:
        - default_namespace (string). Passed in but will be overridden by Chart().namespace if set
        - default_namespace_management_settings (dictionary). Passed in but will be overridden by Chart().namespace_management_settings if set
        """

        try:
            self.__pre_command(default_namespace, default_namespace_management, context)
            self.manage_namespace()

            # Fire the pre_install_hook
            self.pre_install_hook.run()

            try:
                # Perform the upgrade with the arguments
                self.result.response = self.helm.upgrade(self.args, plugin=self.plugin)
            finally:
                self.clean_up_temp_files()
            # Log the stdout response in info

            # Add new chart version to the response
            log_output = self.result.response.stdout
            if self.version:
                log_output = log_output.replace('has been upgraded', f'has been upgraded to {self.version}')
            logging.info(log_output)

            # Fire the post_install_hook
            self.post_install_hook.run()
        except Exception as err:
            logging.debug("Saving encountered error to chart result. See Below:")
            logging.debug("{}".format(err))
            self.result.failed = True
            self.result.error_reason = err
            raise err
        finally:
            if self._deprecation_messages:
                [logging.warning(msg) for msg in self._deprecation_messages]

    def update(self, default_namespace=None, default_namespace_management={}, context=None) -> None:
        """
        Description:
        - Upgrade --install the course charts where this would cause a change in the cluster

        Arguments:
        - default_namespace (string). Passed in but will be overridden by Chart().namespace if set
        - default_namespace_management_settings (dictionary). Passed in but will be overridden by Chart().namespace_management_settings if set
        """

        try:
            if self.requires_update(default_namespace, default_namespace_management, context):
                logging.info(f"Release {self.name} requires updating.")
                self.__pre_command(default_namespace, default_namespace_management, context)
                self.manage_namespace()

                # Fire the pre_install_hook
                self.pre_install_hook.run()

                try:
                    # Perform the upgrade with the arguments
                    self.result.response = self.helm.upgrade(self.args, plugin=self.plugin)
                finally:
                    self.clean_up_temp_files()
                # Log the stdout response in info
                logging.info(self.result.response.stdout)

                # Fire the post_install_hook
                self.post_install_hook.run()
            else:
                logging.info(f"Update not required for {self.release_name}. No Changes")
        except Exception as err:
            logging.debug("Saving encountered error to chart result. See Below:")
            logging.debug("{}".format(err))
            logging.debug(traceback.format_exc())
            self.result.failed = True
            self.result.error_reason = err
            raise err
        finally:
            if self._deprecation_messages:
                [logging.warning(msg) for msg in self._deprecation_messages]

    def template(self, default_namespace=None, default_namespace_management={}, context=None) -> None:
        self.result.response = self.__template_response(default_namespace, default_namespace_management, context)

    def __template_response(self, default_namespace=None, default_namespace_management={}, context=None) -> HelmCmdResponse:
        self.__pre_command(default_namespace, default_namespace_management, context)
        try:
            # Perform the template with the arguments
            return self.helm.template(self.args, plugin=self.plugin)
        except Exception as e:
            logging.debug(traceback.format_exc)
            raise e
        finally:
            self.clean_up_temp_files()

    def get_manifest(self, default_namespace=None, default_namespace_management={}, context=None) -> None:
        # Perform the template with the arguments
        self.result.response = self.__get_manifest_response(default_namespace, default_namespace_management, context)

    def __get_manifest_response(self, default_namespace=None, default_namespace_management={}, context=None) -> HelmCmdResponse:
        self.__pre_command(default_namespace, default_namespace_management, context)
        try:
            # get_manifest needs a different set of args
            self.args = []

            # Set Default args (release name and chart path)
            self._append_arg('{}'.format(self._release_name))

            # Add namespace to args
            self._append_arg('--namespace {}'.format(self.namespace))

            # Add kubecfg context
            if self.context is not None:
                self._append_arg('--kube-context {}'.format(self.context))

            # Add debug arguments
            # No --dry-run flag for get manifest
            for debug_arg in self.debug_args:
                if debug_arg != '--dry-run':
                    self._append_arg(debug_arg)

            # Need this here because of the bespoke arg list
            self._check_env_vars()

            # Perform the template with the arguments
            return self.helm.get_manifest(self.args, plugin=self.plugin)
        except Exception as e:
            raise e
        finally:
            self.clean_up_temp_files()

    def __diff_response(self, default_namespace=None, default_namespace_management={}, context=None) -> SyntaxWarning:
        try:
            manifest_response = self.__get_manifest_response(default_namespace, default_namespace_management, context).stdout
        except HelmClientException as e:
            if "not found" in str(e):
                logging.warn(f"Release {self.release_name} does not exist. Output will be the equal to 'template'")
                manifest_response = ""
            else:
                raise e

        template_response = self.__template_response(default_namespace, default_namespace_management, context).stdout
        diff = manifestDiff(manifest_response, template_response)
        if diff == "":
            logging.info(f"There are no differences in release {self.release_name}")

        return diff

    def requires_update(self, default_namespace=None, default_namespace_management={}, context=None) -> bool:
        """
        Returns true if there is any differences between the installed release and the
        templates that would be generated from this run
        """
        diff = self.__diff_response(
            default_namespace,
            default_namespace_management,
            context
        )
        if diff == "":
            return False
        logging.debug(f"\"{diff}\" != \"\"")
        return True

    def diff(self, default_namespace=None, default_namespace_management={}, context=None) -> None:
        self.result.response = self.__diff_response(
            default_namespace,
            default_namespace_management,
            context
        )

    def _append_arg(self, arg_string):
        for item in arg_string.split(" ", 1):
            self.args.append(item)

    def build_helm_arguments_for_chart(self):
        """
        This method builds all the arguments we'll pass along to the helm
        client once we need to run the install
        """

        # always start off with empty args list
        self.args = []

        # Set Default args (release name and chart path)
        self._append_arg('{}'.format(self._release_name))
        self._append_arg(self.repository.chart_path)

        # Add namespace to args
        self._append_arg('--namespace {}'.format(self.namespace))

        # Add kubecfg context
        if self.context is not None:
            self._append_arg('--kube-context {}'.format(self.context))

        # Add debug arguments
        for debug_arg in self.debug_args:
            self._append_arg(debug_arg)

        # Add the version arguments
        if self.version:
            self._append_arg('--version {}'.format(self.version))

        # TODO Assert that files list is always first
        # Build the list of existing yaml files to use for the helm command
        self.build_files_list()

        # TODO Assert that temp files from course yaml is always after files list, so it takes precedence
        # Build the file arguments from the `values: {}` in course.yml
        self.build_temp_values_files()

    def build_temp_values_files(self):
        """
        This method builds temporary files based on the values: settings
        provided in the course.yml. This effectively keeps type persistence
        between the course.yml and what is passed to helm. If you use set:
        value arguments then you can lose types like int, float and true/false
        """
        # If any values exist
        if self.values:
            # create a temporary file on the file-system but don't clean up after you close it
            with tempfile('w+t', suffix=".yml", delete=False) as temp_yaml:
                # load up the self.values yaml string

                # write the yaml to a string
                yaml_output = yaml_handler.dump(self.values)

                # read the yaml_output and interpolate any variables
                yaml_output = self._interpolate_env_vars_from_string(yaml_output)

                # write the interpolated yaml string and flush it to the file
                temp_yaml.write(yaml_output) and temp_yaml.flush()

                # add the name of the temp file to a list to clean up later
                self._temp_values_file_paths.append(temp_yaml.name)

                # add the name of the file to the helm arguments
                self._append_arg("-f {}".format(temp_yaml.name))

                # log debug info of the contents of the file
                logging.debug("Yaml Values Temp File:\n{}".format(yaml_output))

    def build_files_list(self):
        """
        This method builds the files list for all
        files specified in the course.yml
        Note: values_file must be relative to the course.yml, or declared with an absolute path
        """
        for values_file in self.files:
            self._append_arg("-f {}".format(os.path.join(self.config.course_base_directory, values_file)))

    @staticmethod
    def _interpolate_env_vars_from_string(original_string: str) -> str:
        """
        Accepts string, uses string.Template to apply environment variables to matching variables in the string
        Returns interpolated string or raises error
        """
        # We should never interpolate an env var in a comment. Strip comments from the string before interpolating.
        comments_removed = re.sub(r'([^#]*)(#.*)', r'\g<1>', original_string)
        try:
            return Template(comments_removed).substitute(os.environ)
        except KeyError as e:
            raise ReckonerException(f"Encountered error interpolating environment variables: "
                                    f"Missing requirement environment variable: {e}") from None
        except ValueError as e:
            raise ReckonerException(f"Encountered error \"{e}\" interpolating environment variables. "
                                    "This can happens if you use $(THING) instead of $THING or ${THING}. "
                                    "If you need $(THING) use $$(THING) to escape the `$`") from None
        except Exception as e:
            raise e

    def clean_up_temp_files(self):
        # Clean up all temp files used in the helm run
        for temp_file in self._temp_values_file_paths:
            try:
                os.remove(temp_file)
            except FileNotFoundError:
                logging.debug(f"{temp_file} not found to delete. Ignoring this fact")

    # TODO This needs some documentation and some more thorough testing
    def _format_set(self, key, value):
        """
        Allows nested yaml to be set on the command line of helm.
        Accepts key and value, if value is an ordered dict, recursively
        formats the string properly
        """
        if isinstance(value, dict):
            for new_key, new_value in value.items():
                for k, v in self._format_set("{}.{}".format(key, new_key), new_value):
                    for a, b in self._format_set(k, v):
                        yield a, b
        elif isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, dict):
                    for k, v in self._format_set("{}[{}]".format(key, index), item):
                        yield k, v
                else:
                    yield "{}[{}]".format(key, index), item
        else:
            yield key, value

    def __getattr__(self, key):
        return self._chart.get(key)

    def __str__(self):
        return str(dict(self._chart))

    def _check_env_vars(self):
        """
        accepts list of args
        if any of those appear to be env vars
        and are missing from the environment
        an exception is raised
        """
        for idx in range(len(self.args)):
            self.args[idx] = self._interpolate_env_vars_from_string(self.args[idx])
