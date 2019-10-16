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
import mock
from reckoner.config import Config


class TestConfig(unittest.TestCase):
    @mock.patch('os.getcwd')
    def test_course_base_dir_never_empty(self, mock_dir):
        config = Config()
        config.course_path = 'course.yaml'
        self.assertNotEqual('', config.course_base_directory,
                            "course_base_path has to be None or a real path "
                            "(including '.') because of how it is used in "
                            "Popen. Cannot be an empty string.")

        config.course_path = '/some/full/path/course.yml'
        self.assertEqual('/some/full/path', config.course_base_directory)

        mock_dir.return_value = "/some/fake/path"
        config.course_path = './course.yaml'
        self.assertEqual('/some/fake/path', config.course_base_directory)

        # relative path to /some/fake/path
        config.course_path = '../../relative/course.yml'
        self.assertEqual('/some/relative', config.course_base_directory)
