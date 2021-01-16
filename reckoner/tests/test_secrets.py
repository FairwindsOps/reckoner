import unittest
from unittest import mock

from reckoner.secrets import Secret


class TestSecrets(unittest.TestCase):
    def setUp(self):
        Secret.ALLOWED_BACKENDS = ['testbackend']

    def test_required_attribute(self):

        with self.assertRaises(TypeError):
            Secret(**{})

        with self.assertRaises(TypeError):
            Secret(**{'name': 'testname'})

        with self.assertRaises(TypeError):
            Secret(**{'backend': 'testbackend'})

        Secret(name="foo", backend="testbackend")

    def test_name(self):

        secret = Secret(name="foo", backend="testbackend")
        self.assertEqual(secret.name, "foo")

    def test_allowed_backend(self):

        secret = Secret(name="foo", backend="testbackend")
        with self.assertRaises(TypeError):
            Secret(name="foo", backend="clearlythisisanunsupportedbackend")
