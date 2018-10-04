import unittest
import mock
import logging
from autohelm.autohelm import AutoHelm
from autohelm.config import Config
from autohelm.course import Course
from autohelm.exception import AutoHelmException


# Test properties of the mock
@mock.patch('autohelm.autohelm.Config', autospec=True)
@mock.patch('autohelm.autohelm.Course', autospec=True)
class TestAutoHelmAttributes(unittest.TestCase):
    name = "test-autohelm-attributes"

    def test_config(self, *args):
        autohelm_instance = AutoHelm()
        self.assertTrue(hasattr(autohelm_instance, 'config'))

    def test_course(self, *args):
        autohelm_instance = AutoHelm()
        self.assertTrue(hasattr(autohelm_instance, 'course'))


# Test methods
@mock.patch('autohelm.autohelm.Config', autospec=True)
@mock.patch('autohelm.autohelm.Course', autospec=True)
class TestAutoHelmMethods(unittest.TestCase):
    name = 'test-autohelm-methods'

    def test_install_succeeds(self, *args):
        autohelm_instance = AutoHelm()
        autohelm_instance.config.tiller_present.return_value = True
        autohelm_instance.course.plot.return_value = True
        install_response = autohelm_instance.install()
        self.assertIsInstance(install_response, bool)
        self.assertTrue(install_response)

    def test_install_missing_tiller(self, mock_course, mock_config):
        a = AutoHelm()
        a.config.tiller_present = False

        with self.assertRaises(AutoHelmException):
            a.install()


def __main__():
    unittest.main()
