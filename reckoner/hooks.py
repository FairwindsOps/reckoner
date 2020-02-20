import logging
import traceback

from typing import List

from .config import Config
from .command_line_caller import call
from .exception import ReckonerCommandException


class Hook(object):

    def __init__(self, commands: (str, list) = [], name: str = '', base_directory: str = './'):
        if not isinstance(commands, (str, list)):
            raise AttributeError(
                "Commands for hook must be of type string "
                "or list. {} is not allowed".format(
                    type(commands)
                )
            )
        self._commands = commands
        self._base_directory = base_directory
        self._name = name
        self._config = Config()

    @property
    def name(self) -> str:
        return self._name

    @property
    def commands(self) -> List[str]:
        if isinstance(self._commands, (str)):
            self._commands = [self._commands]

        return self._commands

    @property
    def base_directory(self) -> str:
        return self._base_directory

    @property
    def config(self):
        return self._config

    def run(self):
        if self.config.dryrun:
            logging.warning("Hook not run due to --dry-run: {}".format(self.name))
            return

        for command in self.commands:
            logging.info("Running {} hook...".format(self.name))

            try:
                result = call(
                    command,
                    shell=True,
                    executable="/bin/bash",
                    path=self.base_directory
                )
            except Exception as error:
                # NOTE This block is only used when we cannot send the call or
                #      have other unexpected errors running the command.
                #      The call()->Response should pass a Response object back
                #      even when the exit code != 0.
                logging.error("Critical Error running the command hook.")
                logging.error(error)
                logging.debug(traceback.format_exc())
                raise ReckonerCommandException(
                    "Uncaught exception while running hook "
                    "'{}'".format(command)
                )

            command_successful = result.exitcode == 0

            logging.info("Ran Hook: '{}'".format(result.command_string))
            _output_level = logging.INFO  # The level to log the command output

            if command_successful:
                logging.info("{} hook ran successfully".format(self.name))
            else:
                logging.error("{} hook failed to run".format(self.name))
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
