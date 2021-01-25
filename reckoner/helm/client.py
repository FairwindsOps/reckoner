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

from abc import ABC, abstractmethod
from .provider import HelmProvider
from .command import HelmCommand
import re
import logging


def get_helm_client(helm_arguments, client_version=None, helm_provider=HelmProvider):
    """
    Args:
      client_version (string): Which client class to use
      helm_arguments(list): Arguments passed into the HelmClient class

    Returns:
      Helm3Client


    Raises
      HelmClientException
    """
    try:
        if client_version is not None:
            if client_version == "3":
                return Helm3Client(default_helm_arguments=helm_arguments, provider=helm_provider)
            else:
                raise HelmClientException("Unsupported version explicitly specified: client_version={}".format(client_version))
        else:
            logging.debug('Helm version not declared, detecting version...')
            client3 = Helm3Client(default_helm_arguments=helm_arguments, provider=helm_provider)
            logging.debug('Checking for Helm 3 client')
            detected_version = client3.version
            logging.info('Found Helm Version {}'.format(detected_version))
            return client3
    except HelmClientException as e:
        logging.error(e)
        raise HelmClientException('Could not detect helm version')
    except Exception as e:
        logging.error(e)
        raise HelmClientException('Received an unexpected exception in the helm detection, please see the debug output for details.')


class HelmClient(ABC):
    repository_header_regex = re.compile(r'^NAME\s+URL$')

    @abstractmethod
    def version_regex(self):
        pass

    @abstractmethod
    def global_helm_flags(self):
        pass

    def __init__(self, default_helm_arguments=[], provider=HelmProvider):
        self._default_helm_arguments = self._validate_default_helm_args(default_helm_arguments)
        self._provider = provider

    @property
    def default_helm_arguments(self):
        """The default helm arguments for all commands run through the client."""
        return self._default_helm_arguments

    @property
    def cache(self):
        try:
            return self._cache
        except Exception as e:
            logging.error("Error determining repository cache location. Cannot proceed")
            raise e

    @default_helm_arguments.setter
    def default_helm_arguments(self, value):
        """Setter of the default helm arguments to override"""
        self._default_helm_arguments = value

    def execute(self, command, arguments=[], filter_non_global_flags=False, plugin=None):
        """
        Run the command with the help of the provider.

        return HelmCmdResponse
        """

        default_args = list(self.default_helm_arguments)

        if filter_non_global_flags:
            self._clean_non_global_flags(default_args)

        arguments = default_args + list(arguments)

        # If we need to run wrapped in a plugin, then put that command first, always
        if plugin:
            arguments = [command] + arguments
            command = plugin

        helm_command = HelmCommand(
            command=command,
            arguments=arguments,
        )
        response = self._provider.execute(helm_command)
        if response.succeeded:
            return response
        else:
            err = HelmClientException('Command Failed with output below:\nSTDOUT: {}\nSTDERR: {}\nCOMMAND: {}'.format(
                response.stdout, response.stderr, response.command))
            raise err

    @property
    def repositories(self):
        logging.debug("Listing repositories configured on helm client")
        repository_names = []
        try:
            raw_repositories = self.execute('repo', ['list'], filter_non_global_flags=True).stdout
        except HelmClientException:
            logging.warning("Error getting repositories from client, maybe none have been initialized?")
            return repository_names
        for line in raw_repositories.splitlines():
            # Try to filter out the header line as a viable repo name
            if HelmClient.repository_header_regex.match(str(line)):
                continue
            # If the line is blank
            if not line:
                continue

            repository_names.append(line.split()[0])

        return repository_names

    def check_helm_command(self):
        return self.execute("help", [], filter_non_global_flags=True).succeeded

    def upgrade(self, args, install=True, plugin=None):
        if install:
            arguments = ['--install'] + args
        else:
            arguments = args
        return self.execute("upgrade", arguments, plugin=plugin)

    def template(self, args, plugin=None):
        return self.execute("template", args, plugin=plugin)

    def get_manifest(self, args, plugin=None):
        return self.execute("get manifest", args, plugin=plugin)

    def get_values(self, args, plugin=None):
        return self.execute("get values -o json", args, plugin=plugin)

    def list_releases(self, args, plugin=None):
        return self.execute("list -o json", args, plugin=plugin)

    def rollback(self, release):
        raise NotImplementedError(
            """This is known bad. If you see this error then you are likely implementing the solution :)"""
        )

    def dependency_update(self, chart_path):
        """Function to update chart dependencies"""
        return self.execute('dependency', ['update', chart_path], filter_non_global_flags=True)

    def repo_update(self):
        """Function to update all the repositories"""
        return self.execute('repo', ['update'], filter_non_global_flags=True)

    def repo_add(self, name, url):
        """Function add repositories to helm via command line"""
        return self.execute('repo', ['add', name, url], filter_non_global_flags=True)

    @classmethod
    def _clean_non_global_flags(self, list_of_args):
        """Return a copy of the set arguments without any non-global flags - do not edit the instance of default_helm_args"""
        # Filtering out non-global helm flags -- this is to try and support
        # setting all-encompassing flags like `tiller-namespace` but avoiding
        # passing subcommand specific flags to commands that don't support
        # them.
        # Example: `helm upgrade --install --recreate-pods ...` but we don't
        #          want to run `helm repo add --recreate-pods repo-name ...`
        #
        # TODO: This is a slow implementation but it's fine for cli (presumably)
        #       Bad nesting - there's a better pattern for sure
        #
        # Looping logic:
        #   1. run through each argument in defaults
        #   2. Set known global false for item's iteration
        #   3. For each item in defaults check if it matches a known good global argument
        #   4. if matches note it, set known good = true and break inner iteration
        #   5. if inner iter doesn't find global param then known_global is bad and delete it from list
        for arg in list_of_args:
            logging.debug('Processing {} argument'.format(arg))
            known_global = False
            for valid in self.global_helm_flags:
                if re.findall(r"--{}(\s|$)+".format(valid), arg):
                    known_global = True
                    break  # break out of loop and stop searching for valids for this one argument
            if known_global:
                logging.debug('This argument {} was found in valid arguments: {}, keeping in list.'.format(arg, ' '.join(self.global_helm_flags)))
            else:
                list_of_args.remove(arg)
                logging.debug('This argument {} was not found in valid arguments: {}, removing from list.'.format(arg, ' '.join(self.global_helm_flags)))

    @staticmethod
    def _validate_default_helm_args(helm_args):
        # Allow class to be instantiated with default_helm_arguments to be None
        if helm_args is None:
            helm_args = []
        # Validate that we're providing an iterator for default helm args
        # also check for type string, python3 strings contain __iter__
        if not hasattr(helm_args, '__iter__') or isinstance(helm_args, str):
            logging.error("This class is being instantiated without an iterator for default_helm_args.")
            raise ValueError('default_helm_arguments needs to be an iterator')

        return helm_args

    @abstractmethod
    def version(self):
        pass


class HelmClientException(Exception):
    pass


class HelmVersionException(Exception):
    pass


class Helm3Client(HelmClient):
    version_regex = re.compile(r'v([0-9\.]+)([\-,\+][a-zA-Z]+)(\+g[0-9a-f]+)?')
    global_helm_flags = ['debug', 'home', 'host', 'kube-context', 'kubeconfig']

    @property
    def version(self):
        return self._get_version()

    @property
    def _cache(self):
        response = self.execute("env", filter_non_global_flags=True)
        # Get the value of the HELM_REPOSITORY_CACHE from the helm env command
        return [_var_line.split('=')[1] for _var_line in response.stdout.splitlines() if 'HELM_REPOSITORY_CACHE' in _var_line][0].replace('"', '')

    def _get_version(self):
        get_ver = self.execute("version", arguments=['--short'], filter_non_global_flags=True)
        ver = self._find_version(get_ver.stdout)
        if ver is None:
            raise HelmClientException(
                """Could not find version!! Could the helm response format have changed?
                STDOUT: {}
                STDERR: {}
                COMMAND: {}""".format(get_ver.stdout, get_ver.stderr, get_ver.command)
            )
        return ver

    @staticmethod
    def _find_version(raw_version):
        ver = Helm3Client.version_regex.search(str(raw_version))
        if ver:
            return ver.group(1)
        else:
            return None
