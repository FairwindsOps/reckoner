
import os
import logging

from . import call
from repository import Repository

class Helm(object):

    helm_binary = 'helm'

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
        _repositories = []
        logging.debug("Getting installed repositories: {}".format(self._installed_repositories))
        r = self.repo_list()
        for repo in [line.split() for line in r.stdout.split('\n')[1:-1]]:
            _repo = {'name': repo[0], 'url': repo[1]}
            _repositories.append(Repository(_repo))
        return _repositories

    @property
    def client_version(self):
        r = self.version("--client")
        return r.stdout.replace('Client: &version.Version', '').split(',')[0].split(':')[1].replace('v', '').replace('"', '')

    @property
    def server_version(self):
        r = self.version("--server")
        return r.stdout.replace('Server: &version.Version', '').split(',')[0].split(':')[1].replace('v', '').replace('"', '')

    @property
    def releases(self):

        r = self.list()
        _releases = Releases()

        for release in r.stdout.splitlines()[1:]:
            _releases.append(Release(*[field.strip() for field in release.split('\t')]))

        return _releases


class Releases(object):

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
        return self._deployed

    @property
    def failed(self):
        return self._failed

    def __iter__(self):
        return iter(self._failed + self._deployed + self._all)

    def __str__(self):
        return str([str(rel) for rel in self])


class Release(object):

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
        if self.status == 'DEPLOYED':
            return True
        return False

    @property    
    def failed(self):
        if self.status == 'FAILED':
            return True
        return False

    def rollback(self):
        return self.helm.rollback(self.name, self.revision)


    
