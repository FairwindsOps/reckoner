
import os
import logging

from . import call
from repository import Repository
from exception import ReckonerCommandException


class HelmException(Exception):
    pass


class Helm(object):
    """
    Description:
    - Interface like class to the helm binary.
    - Most helm calls are not defined as method, but any helm command can be
    called by an instance of this class with the command name as the method
    name and positional argumenst passed a list. Multiword commands are
    '_' delimited
    - example: Helm().repo_update() will call `helm repo update`
    - example: Helm().upgrade(['--install','stable/redis'])
    will call `helm upgrade --install stable/redis"

    Attributes:
    - client_version: Shortcut to  `Helm().version('--client')
    - server_version: Shortcut to  `Helm().version('--server')
    - releases: Instance of Releases() with all current helm releases
    - repositories: list of Repository() instances that are
    currently configured

    """
    helm_binary = 'helm'

    def __init__(self):

        try:
            r = self.help()
        except ReckonerCommandException, e:
            raise HelmException("Helm not installed properly")

    def _call(self, args):
        args.insert(0, self.helm_binary)
        return call(args)

    def __getattr__(self, name):

        def method(*args, **kwargs):
            command = name.split("_")
            for arg in args:
                command.append(arg)

            for key, value in kwargs.iteritems():
                command.append("--{}={}".format(key, value))
            r = self._call(command)
            return r

        return method

    @property
    def repositories(self):
        """list of Repository() instances as the currently configured repositories"""
        _repositories = []
        r = self.repo_list()
        for repo in [line.split() for line in r.stdout.split('\n')[1:-1]]:
            _repo = {'name': repo[0], 'url': repo[1]}
            _repositories.append(Repository(_repo))
        return _repositories

    @property
    def client_version(self):
        """ helm client version """
        try:
            r = self.version("--client")
            return r.stdout.replace('Client: &version.Version', '').split(',')[0].split(':')[1].replace('v', '').replace('"', '')
        except ReckonerCommandException, e:
            pass

    @property
    def server_version(self):
        """ helm tiller server version"""
        try:
            r = self.version("--server")
            return r.stdout.replace('Server: &version.Version', '').split(',')[0].split(':')[1].replace('v', '').replace('"', '')
        except ReckonerCommandException, e:
            pass

    @property
    def releases(self):
        """ Releases() instance with current releases """
        r = self.list()
        _releases = Releases()

        for release in r.stdout.splitlines()[1:]:
            _releases.append(Release(*[field.strip() for field in release.split('\t')]))

        return _releases

    def upgrade(self, args):
        initial_args = ['upgrade', '--install']
        try:
            self._call(initial_args + args)
        except ReckonerCommandException, e:
            logging.error(e)
            raise e


class Releases(object):
    """
    Description:
    - Container class of Release() instances
    - Duck type list

    Attributes:
    - deployed: Returns list of Release() with `DEPLOYED` status
    - failed: Return list of Release() with `FAILED` status

    """

    def __init__(self):
        self._deployed = []
        self._failed = []
        self._all = []

    def append(self, release):
        if release.deployed:
            self._deployed.append(release)
            return

        if release.failed:
            self.failed.append(release)
            return

        self._all.append(release)

    @property
    def deployed(self):
        """ Returns list of Release() with `DEPLOYED` status """
        return self._deployed

    @property
    def failed(self):
        """ Return list of Release() with `FAILED` status"""
        return self._failed

    def __iter__(self):
        return iter(self._failed + self._deployed + self._all)

    def __str__(self):
        return str([str(rel) for rel in self])


class Release(object):
    """
    Description:
    -  Active helm release

    Arguments:
    - name: releae name
    - revision: revisiong number
    - updated: last updated date
    - status: Helm status
    - chart: chart name
    - app-version: chart version
    - namespace: installed namespace

    Attributes:
    - deployed: Returns list of Release() with `DEPLOYED` status
    - failed: Return list of Release() with `FAILED` status

    """

    def __init__(self, name, revision, updated, status, chart, app_version, namespace):
        self._dict = {
            'name': name,
            'revision': revision,
            'updated': updated,
            'status': status,
            'chart': chart,
            'app_version': app_version,
            'namespace': namespace,
        }

        self.helm = Helm()

    def __getattr__(self, key):
        return self._dict.get(key)

    def __str__(self):
        return str(self._dict)

    @property
    def deployed(self):
        """ Boolean test for Releas().status """
        if self.status == 'DEPLOYED':
            return True
        return False

    @property
    def failed(self):
        """ Boolean test for Release().status """
        if self.status == 'FAILED':
            return True
        return False

    def rollback(self):
        """ Roll back current release """
        return self.helm.rollback(self.name, self.revision)
