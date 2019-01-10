import mock
import unittest
from reckoner.exception import MinimumVersionException
from reckoner.course import Course


@mock.patch('reckoner.repository.Repository', autospec=True)
@mock.patch('reckoner.course.sys')
@mock.patch('reckoner.course.yaml', autospec=True)
@mock.patch('reckoner.course.HelmClient', autospec=True)
@mock.patch('reckoner.course.Config', autospec=True)
class TestMinVersion(unittest.TestCase):
    def test_init_error_fails_min_version_reckoner(self, configMock, helmClientMock, yamlLoadMock, sysMock, repoMock):
        """Tests that minimum version will throw an exit."""
        c = configMock()
        c.helm_args = ['provided args']
        c.local_development = False

        yamlLoadMock.load.return_value = {
            'repositories': {
                'name': {},
            },
            'helm_args': None,
            'minimum_versions': {
                'reckoner': '1000.1000.1000',  # minimum version needed
                # find the version of reckoner at meta.py __version__
            }
        }

        sysMock.exit.return_value = None

        course = Course(None)

        sysMock.exit.assert_called_once
        return True

    def test_init_error_fails_min_version_helm(self, configMock, helmClientMock, yamlLoadMock, sysMock, repoMock):
        """Tests that minimum version will throw an exit."""
        c = configMock()
        c.helm_args = ['provided args']
        c.local_development = False

        h = helmClientMock()
        h.client_version = '0.0.1'

        yamlLoadMock.load.return_value = {
            'repositories': {
                'name': {},
            },
            'helm_args': None,
            'minimum_versions': {
                'helm': '1000.1000.1000',  # minimum version needed
            }
        }

        sysMock.exit.return_value = None

        course = Course(None)

        sysMock.exit.assert_called_once
        return True
