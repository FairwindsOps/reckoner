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


import logging
import traceback

from typing import List

from .base import SecretProvider
from ...command_line_caller import call
from ...exception import ReckonerCommandException

logger = logging.getLogger(__name__)


class ShellExecutor(SecretProvider):
    """
    Secret Provider shell commands
    Required Arguments:
    `script`: The name of the Parameter Store Value
    Optional Arguments:
    `shell`: Default `True`. When True, commands are executed in a shell.
    `executable`: Default `/bin/bash`. The shell environment in which to run.
    `path`: Default `./`. The direcotry to run the script in.

    """

    def __init__(self, script: str, shell: bool = True, executable: str = "/bin/bash", path: str = "./") -> None:
        self.script = script
        self.shell = shell
        self.executable = executable
        self.path = path

    def get_value(self):
        try:
            result = call(
                self.script,
                shell=self.shell,
                executable=self.executable,
                path=self.path
            )
        except Exception as error:
            # NOTE This block is only used when we cannot send the call or
            #      have other unexpected errors running the command.
            #      The call()->Response should pass a Response object back
            #      even when the exit code != 0.
            logger.error("Critical Error running shell command.")
            logger.error(error)
            logger.debug(traceback.format_exc())
            raise ReckonerCommandException(
                "Uncaught exception while running shell command "
                "'{}'".format(self.script)
            )

        logger.debug("'Shell' type secret debug:")
        logger.debug(f"stdout: {result.stdout}")
        logger.debug(f"stderr: {result.stderr}")

        # Always raise an error after failures
        if result.stderr or result.exitcode != 0:
            raise ReckonerCommandException(
                f"'Shell' type secret command ({result.command_string}) exited with an error.",
                stdout=result.stdout,
                stderr=result.stderr,
            )

        return result.stdout.strip()
