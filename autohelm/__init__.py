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
import exception


def call(args):
    """
    Wrapper utility function for subprocess.Popen.
    Accepts list: `args`
    Return tuple: `(stdout, stderr, exitcode)`
    """
    logging.debug(' '.join(args))
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    exitcode = p.returncode

    if exitcode > 0:
        raise exception.AutoHelmCommandException(
            "Error with subprocess call: {})"
            .format(' '.join(args)), stdout, stderr, exitcode
            )
    return stdout, stderr, exitcode
