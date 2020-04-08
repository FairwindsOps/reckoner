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

import unittest
from unittest import mock

from reckoner.kube import NamespaceManager


@mock.patch('reckoner.kube.client', autospec=True)
@mock.patch('reckoner.kube.config', autospec=True)
class TestNamespaceManager(unittest.TestCase):

    def setUp(self):
        pass

    def test_full_monty(self, kube_client_mock, kube_config_mock):

        settings = {
            "metadata":
            {
                "annotations":
                {
                    "one": "1ne",
                    "two": "2wo"
                },
                "labels":
                {
                    "one": "1ne",
                    "two": "2wo"
                }
            },
            "settings": {"overwrite": True}
        }

        _ns_manager = NamespaceManager('test', settings)

        self.assertTrue(_ns_manager.overwrite)
        self.assertEqual(_ns_manager.metadata, {
            "annotations":
                {
                    "one": "1ne",
                    "two": "2wo"
                },
            "labels":
                {
                    "one": "1ne",
                    "two": "2wo"
                }
        })

        self.assertEqual(_ns_manager.namespace_name, 'test')

    def test_overwrite_false(self, kube_client_mock, kube_config_mock):

        settings = {
            "settings": {"overwrite": False}
        }

        _ns_manager = NamespaceManager('test', settings)

        self.assertFalse(_ns_manager.overwrite)
        self.assertEqual(_ns_manager.metadata, {})

    def test_overwrite_false_when_not_specified(self, kube_client_mock, kube_config_mock):

        settings = {
            "metadata": {}
        }

        _ns_manager = NamespaceManager('test', settings)

        self.assertFalse(_ns_manager.overwrite)
        self.assertEqual(_ns_manager.metadata, {})
