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
# limitations under the License.__init__.py

import subprocess
import logging

from exception import ReckonerCommandException


class Response(object):
    """
    Description:
    - Utility class to simplify the results from call()

    Arguments:
    - stdout(string)
    - stderr (string)
    - exitcode (sting,int)

    Attributes:
    - stdout
    - stderr
    - exitcode

    Returns:
    - Instance of Response() is truthy where Reponse.exitcode == 0
    - Instance Response() is falsey where Reponse.exitcode != 0
    """

    def __init__(self, stdout, stderr, exitcode):

        self._dict = {}
        self._dict['stdout'] = stdout
        self._dict['stderr'] = stderr
        self._dict['exitcode'] = exitcode

    def __getattr__(self, name):
        return self._dict.get(name)

    def __str__(self):
        return str(self._dict)

    def __bool__(self):
        return not self._dict['exitcode']

    def __eq__(self, other):
        return self._dict == other._dict


def call(args, shell=False, executable=None):
    """
    Description:
    - Wrapper for subprocess.Popen. Joins `args` and passes
    to `subprocess.Popen`

    Arguments: 
    - args (list or string)

    Returns:
    - Instance of Response()
    """
    if type(args) == str:
        args_string = args
    else:
        args_string = ' '.join(args)
    logging.debug(args_string)
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell, executable=executable)
    stdout, stderr = p.communicate()
    exitcode = p.returncode

    if exitcode > 0:
        raise ReckonerCommandException("Error with subprocess call: {}".format(args_string), stdout, stderr, exitcode)
    return Response(stdout, stderr, exitcode)
