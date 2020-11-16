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

from reckoner.command_line_caller import call
from .cmd_response import HelmCmdResponse
from reckoner.config import Config


class HelmProvider(object):
    """
    HelmProvider is intended to be the simple way to run commands against helm and have standard responses.

    Interface for a provider:
    - class method of execute: returns a HelmCmdResponse
    """

    def __init__(
            self,
            helm_command,
            helm_binary="helm"):
        """Requires protocol of HelmCommand to respond to command and arguments."""
        self._helm_command = helm_command
        self._helm_binary = helm_binary

    # TODO: Investigate if this is really the implementation i need for a provider (class methods with no access to the instance)
    @classmethod
    def execute(cls, helm_command):
        """Executed the command provided in the init. Only allowed to be executed once!"""

        # initialize the instance of the provider
        instance = cls(helm_command)

        # start by creating a command line arguments list with the command being first
        args = list([instance._helm_binary])

        # if command has a space in it (like get manifests), split on space
        # and append each segment as it's own list item to make `call` happy
        for command_segment in instance._helm_command.command.split(' '):
            args.append(command_segment)

        for arg in instance._helm_command.arguments:
            args.append(arg)

        call_response = call(args, path=Config().course_base_directory)

        return HelmCmdResponse(
            exit_code=call_response.exitcode,
            stdout=call_response.stdout,
            stderr=call_response.stderr,
            command=helm_command,
        )
