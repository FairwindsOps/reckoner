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


class HelmCmdResponse(object):
    """HelmCmdResponse has the result of the command with the exit_code, stderr and stdout. Also includes the originally run command."""

    def __init__(self, exit_code, stderr, stdout, command):
        self._stderr = stderr
        self._stdout = stdout
        self._exit_code = exit_code
        self._command = command

    @property
    def exit_code(self):
        return self._exit_code

    @property
    def stderr(self):
        return self._stderr

    @property
    def stdout(self):
        return self._stdout

    @property
    def command(self):
        return self._command

    @property
    def succeeded(self):
        return self._exit_code == 0
