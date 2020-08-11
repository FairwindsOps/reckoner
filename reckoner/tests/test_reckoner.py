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

from reckoner.helm.client import HelmClientException
from reckoner.reckoner import Reckoner, ReckonerInstallResults
from reckoner.chart import ChartResult
from reckoner.exception import ReckonerCommandException, NoChartsToInstall, ReckonerException
from reckoner.helm.client import get_helm_client


@mock.patch('reckoner.reckoner.Course')
@mock.patch('reckoner.course.get_helm_client')
@mock.patch('reckoner.reckoner.Config', autospec=True)
class TestReckoner(unittest.TestCase):
    """Test reckoner class"""

    def test_reckoner_raises_no_charts_correctly(self, mock_config, mock_helm_client, mock_course):
        """Assure we fail when NoChartsToInstall is bubbled up"""
        course_instance = mock_course()
        course_instance.plot.side_effect = [NoChartsToInstall('none')]

        reckoner_instance = Reckoner()
        with self.assertRaises(ReckonerCommandException):
            reckoner_instance.install()


class TestReckonerInstallResults(unittest.TestCase):

    def test_blank_results(self):
        r = ReckonerInstallResults()
        self.assertEqual(len(r.results), 0)
        self.assertFalse(r.has_errors)

    def test_has_errors(self):
        r = ReckonerInstallResults()
        r.add_result(ChartResult(name="fake-result", failed=False, error_reason="", response=None))
        self.assertFalse(r.has_errors)

        r = ReckonerInstallResults()
        r.add_result(ChartResult(name="failed-result", failed=True, error_reason="somereason", response=None))
        self.assertTrue(r.has_errors)

    def test_results_with_errors(self):
        r = ReckonerInstallResults()
        r.add_result(ChartResult(name="good-result", failed=False, error_reason="", response=None))
        r.add_result(ChartResult(name="failed", failed=True, error_reason="failed install", response=None))

        self.assertEqual(len(r.results_with_errors), 1)
