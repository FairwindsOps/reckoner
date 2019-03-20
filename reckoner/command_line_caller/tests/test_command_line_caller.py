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

import unittest
from reckoner.command_line_caller import Response


class TestResponse(unittest.TestCase):
    def test_properties(self):
        required_attrs = {
            'stdout': 'stdout value',
            'stderr': 'stderr value',
            'exitcode': 0,
            'command_string': 'command -that -ran',
        }
        response = Response(**required_attrs)
        for attr, value in list(required_attrs.items()):
            self.assertEqual(getattr(response, attr), value)

    def test_bool(self):
        response = Response('', '', 127, '')
        self.assertFalse(response, "Any response where exitcode is not 0 should return false")

        response = Response('', '', 0, '')
        self.assertTrue(response, "All responses with exitcode 0 should return True")
