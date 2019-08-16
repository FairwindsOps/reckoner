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

from ruamel.yaml import YAML
from io import BufferedReader, StringIO


class Handler(object):
    """Yaml handler class for loading, and dumping yaml consistently"""
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.allow_unicode = True
    yaml.allow_duplicate_keys = True

    @classmethod
    def load(cls, yaml_file: BufferedReader):
        return cls.yaml.load(yaml_file)

    @classmethod
    def dump(cls, data: dict) -> str:
        temp_file = StringIO()
        cls.yaml.dump(data, temp_file)
        return temp_file.getvalue()
