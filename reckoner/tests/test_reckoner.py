import unittest
import mock

from reckoner.helm.client import HelmClientException
from reckoner.reckoner import Reckoner
from reckoner.exception import ReckonerCommandException, NoChartsToInstall


@mock.patch('reckoner.reckoner.Course')
@mock.patch('reckoner.reckoner.HelmClient')
@mock.patch('reckoner.reckoner.Config', autospec=True)
class TestReckoner(unittest.TestCase):
    """Test reckoner class"""

    @mock.patch('reckoner.reckoner.sys')
    def test_reckoner_raises_errors_on_bad_client_response(self, mock_sys, mock_config, mock_helm_client, *args):
        """Make sure helm client exceptions are raised"""
        mock_sys.exit.return_value = True

        # Check helm client exception checking command
        helm_instance = mock_helm_client()
        helm_instance.check_helm_command.side_effect = [HelmClientException('broken')]
        Reckoner()
        mock_sys.exit.assert_called_once()
        helm_instance.check_helm_command.assert_called_once()

    def test_reckoner_raises_no_charts_correctly(self, mock_config, mock_helm_client, mock_course):
        """Assure we fail when NoChartsToInstall is bubbled up"""
        course_instance = mock_course()
        course_instance.plot.side_effect = [NoChartsToInstall('none')]

        reckoner_instance = Reckoner()
        with self.assertRaises(ReckonerCommandException):
            reckoner_instance.install()
