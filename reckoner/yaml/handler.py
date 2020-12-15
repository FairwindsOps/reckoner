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

from ruyaml.constructor import DuplicateKeyError
from ruyaml import YAML
from reckoner.exception import ReckonerConfigException
import logging
from io import BufferedReader, StringIO


class Handler(object):
    """Yaml handler class for loading, and dumping yaml consistently"""
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.allow_unicode = True
    yaml.allow_duplicate_keys = False

    @classmethod
    def load(cls, yaml_file: BufferedReader):
        try:
            y = cls.yaml.load(yaml_file)
        except DuplicateKeyError as err:
            logging.error(_clean_duplicate_key_message(str(err)))
            raise ReckonerConfigException(
                "Duplicate key found while loading your course YAML, please remove the duplicate key shown above.")
        except Exception as err:
            logging.error("Unexpected error when parsing yaml. See debug for more details.")
            logging.debug(err)
            raise err
        return y

    @classmethod
    def load_all(cls, yaml_file: BufferedReader):
        try:
            y = cls.yaml.load_all(yaml_file)
        except DuplicateKeyError as err:
            logging.error(_clean_duplicate_key_message(str(err)))
            raise ReckonerConfigException(
                "Duplicate key found while loading your course YAML, please remove the duplicate key shown above.")
        except Exception as err:
            logging.error("Unexpected error when parsing yaml. See debug for more details.")
            logging.debug(err)
            raise err
        return y

    @classmethod
    def dump(cls, data: dict) -> str:
        temp_file = StringIO()
        cls.yaml.dump(data, temp_file)
        return temp_file.getvalue()

    @classmethod
    def dump_all(cls, data: dict) -> str:
        temp_file = StringIO()
        cls.yaml.dump_all(data, temp_file)
        return temp_file.getvalue()


def _clean_duplicate_key_message(msg: str):
    unwanted = """
To suppress this check see:
    http://yaml.readthedocs.io/en/latest/api.html#duplicate-keys

Duplicate keys will become an error in future releases, and are errors
by default when using the new API.
"""
    return msg.replace(unwanted, '')
