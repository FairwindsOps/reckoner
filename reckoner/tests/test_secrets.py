import unittest
from unittest import mock

from reckoner.secrets import Secret
from reckoner.secrets.providers.base import SecretProvider
from reckoner.secrets.providers import *
from reckoner.exception import ReckonerCommandException


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
        self.assertEqual(str(secret), "foo")

    def test_allowed_backend(self):

        Secret(name="foo", backend="testbackend")
        with self.assertRaises(TypeError):
            Secret(name="foo", backend="clearlythisisanunsupportedbackend")

    def test_value(self):
        secret = Secret(name="foo", backend="testbackend")
        secret._value = "test_value"
        self.assertEqual(secret.value, "test_value")

    def test_provider_call(self):
        secret = Secret(name="foo", backend="testbackend")

        class testbackedprovider(SecretProvider):
            def __init__(self,**kwargs):
                pass

            def get_value(self):
                return "testbackendprovider.get_value"

        secret._provider = testbackedprovider

        self.assertEqual(secret.value, "testbackendprovider.get_value")


class TestAWSParameterStoreProvider(unittest.TestCase):

    def test_provider_instantiation_with_region(self):
        provider = AWSParameterStore(**{"parameter_name": "/test/parameter/foo", "region": "us-left-3"})
        self.assertEqual(provider.ssm_parameter_name, '/test/parameter/foo')
        self.assertEqual(provider.ssm_client_extra_args['region_name'], 'us-left-3')

    def test_provider_instantiation_without_region(self):
        provider = AWSParameterStore(**{"parameter_name": "/test/parameter/foo"})
        self.assertEqual(provider.ssm_parameter_name, '/test/parameter/foo')
        self.assertEqual(provider.ssm_client_extra_args, {})


class TestShellExecutorProvider(unittest.TestCase):

    def test_shell_executor_with_string(self):
        test_script_string = "echo 'test-exec' | grep exec | awk -F'-' '{ print $1 }'"
        provider = ShellExecutor(test_script_string)
        self.assertEqual(provider.get_value(), 'test')

    def test_shell_executor_with_bad_call(self):
        test_script_string = "notarealbinary"
        provider = ShellExecutor(test_script_string)

        with self.assertRaises(ReckonerCommandException):
            provider.get_value()

    def test_shell_executor_with_bad_exit_code(self):
        test_script_string = "echo test | grep -q nottest"
        provider = ShellExecutor(test_script_string)
        with self.assertRaises(ReckonerCommandException):
            provider.get_value()
