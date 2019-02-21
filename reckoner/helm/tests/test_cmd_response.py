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

from reckoner.helm.cmd_response import HelmCmdResponse


class TestHelmCmdResponse(object):
    def test_succeeded_method(self):
        assert HelmCmdResponse(0, None, None, None).succeeded == True
        assert HelmCmdResponse(1, None, None, None).succeeded == False

    def test_properties(self):
        resp = HelmCmdResponse(0, '', '', '')
        for attr in ['exit_code', 'stdout', 'stderr', 'command']:
            assert getattr(resp, attr) != None
