# Copyright 2019 ReactiveOps Inc
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

# NOTE This isn't actually used afaik - it's brought over from original helm.py
# The only functionality that is referenced is rollback. I am keeping it in here
# for later refactor when we address Rollback functionality again
from .helm.client import HelmClient


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
    - name: release name
    - revision: revisioning number
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

        self.helm = HelmClient()

    def __getattr__(self, key):
        return self._dict.get(key)

    def __str__(self):
        return str(self._dict)

    @property
    def deployed(self):
        """Boolean test for Releas().status."""
        if self.status == 'DEPLOYED':
            return True
        return False

    @property
    def failed(self):
        """Boolean test for Release().status"""
        if self.status == 'FAILED':
            return True
        return False

    def rollback(self):
        """ Roll back current release """
        return self.helm.rollback(self.name, self.revision)
