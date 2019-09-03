from reckoner.yaml.handler import Handler
from reckoner.exception import ReckonerConfigException
from io import StringIO
from string import Template

import unittest


class TestYamlClassMethods(unittest.TestCase):
    def setUp(self):
        self.yaml_data = StringIO('''---
my_key: "some_val"
int: 1234
float: 1.02
bool: true
mystring: "mystring"
string_of_int: "1234"
string_of_bool: "False"
''')
        self.bad_yaml_data = StringIO('{--<df\n]')
        self.example_dict = {
            "my_key": "some_val",
            "int": 1234,
            "float": 1.02,
            "bool": True,
            "mystring": "mystring",
            "string_of_int": "1234",
            "string_of_bool": "False",
        }

    def test_load(self):
        """Assert that load can load valid yaml"""
        yaml = Handler.load(self.yaml_data)
        self.assertEqual(yaml["my_key"], "some_val")
        self.assertEqual(yaml["bool"], True)

    def test_load_errors(self):
        """Assert that load fails on invalid yaml"""
        with self.assertRaises(Exception):
            Handler.load(self.bad_yaml_data)

    def test_load_duplicate_keys(self):
        """Assert that the initial key defined, of duplicate keys, takes precedence"""
        with_duplicate = StringIO("{}\nbool: false\n".format(self.yaml_data.getvalue()))
        with self.assertRaises(ReckonerConfigException):
            Handler.load(with_duplicate)

    def test_dump(self):
        """Assert that dump returns a string that is valid yaml"""
        # Read the dict into a yaml file string via stringIO
        yaml_file = StringIO(Handler.dump(self.example_dict))
        # Read the stringio "file" into a dict again
        data = Handler.load(yaml_file)

        # Assert that the data that was dumped and loaded is completely equal
        self.assertDictEqual(data, self.example_dict)

    def test_load_to_dump_to_load(self):
        """Assert when we load data and then dump and then reload it's equal"""
        data = Handler.load(self.yaml_data)
        yaml = StringIO(Handler.dump(data))
        final_data = Handler.load(yaml)

        self.assertDictEqual(data, final_data)

    def test_string_replacements(self):
        """Mimic the string replacement used for env var interpolation in charts"""
        # Load a new yaml file with an "env var" of replacethis: ""
        yaml_file = self.yaml_data.getvalue() + '\nexpect_string: "${REPLACEME}"\nexpect_bool: ${REPLACEME}\n'

        # Serialize the yaml into memory
        initial_read = Handler.load(StringIO(yaml_file))

        # Redump the yaml (mimicing the temp file yaml for helm)
        initial_dump = Handler.dump(initial_read)

        # Do a string replacement on the env var in the new dump
        yaml_file = Template(initial_dump).substitute({'REPLACEME': 'true'})

        # Re-read the replaced string
        data = Handler.load(StringIO(yaml_file))

        # Test that type is consistent
        self.assertIsInstance(data["expect_bool"], bool, "Expected 'expect_bool' to be a bool due to no quotes in the initial yaml.")
        self.assertIsInstance(data["expect_string"], str, "Expected 'expect_string' to remain a string because it was quoted in the initial yaml.")
