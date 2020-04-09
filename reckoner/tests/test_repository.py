import unittest
from unittest.mock import patch

from reckoner.repository import Repository

class TestRepository(unittest.TestCase):
    @patch('reckoner.helm.client.Helm3Client', autospec=True)
    def test_add_repo_for_remote_chart(self, helm_client):
        repo = Repository(dict(name='testrepo', url='url'), helm_client)
        repo.install('test_chart')
        helm_client.repo_add.assert_called()

    @patch('reckoner.helm.client.Helm3Client', autospec=True)
    def test_do_not_add_repo_for_local_chart(self, helm_client):
        repo = Repository(dict(name='testrepo', path='../'), helm_client)
        repo.install('test_chart')
        helm_client.repo_add.assert_not_called()

    @patch('reckoner.helm.client.Helm3Client', autospec=True)
    def test_do_not_add_repo_for_git_chart(self, helm_client):
        with patch('reckoner.repository.Repository._fetch_from_git'):
            repo = Repository(dict(name='testrepo', git='../'), helm_client)
            repo.install('test_chart')
            helm_client.repo_add.assert_not_called()

