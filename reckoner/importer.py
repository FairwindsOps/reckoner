# -- coding: utf-8 --

# Copyright 2019 FairwindsOps Inc
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

import json
import logging

from .helm.client import get_helm_client
from .config import Config
from .exception import ReckonerException

logger = logger = logging.getLogger(__name__)


def get_values(release: str, namespace: str) -> dict:
    """
    Gets the user supplied values from the helm release specified
    Arguments:
    release: The name of the release to import. No default.
    namespace: The namespace of the release to import. No default.

    Returns:
    Dictionary of release values
    """
    helm_client = get_helm_client(helm_arguments=Config().helm_args)
    response = helm_client.get_values(
        [f'--namespace={namespace}', release]
    )
    if response.exit_code:
        raise ReckonerException(f'Error getting values: {response.stderr}')

    return json.loads(response.stdout)


def list_release(release: str, namespace: str) -> dict:
    """
    Gets chart name and chart version information about the release specified
    Arguments:
    release: The name of the release to import. No default.
    namespace: The namespace of the release to import. No default.

    Returns:
    Dictionary of realease information
    """
    helm_client = get_helm_client(helm_arguments=Config().helm_args)
    response = helm_client.list_releases(
        [f'--namespace={namespace}']
    )

    if response.exit_code:
        raise ReckonerException(f'Error getting release: {response.stderr}')

    for _release in json.loads(response.stdout):
        if _release.get('name') == release:
            return _release

    raise ReckonerException(f"Release {release} not found in {namespace}")


def draft_release(release: str, namespace: str, repository: str) -> dict:
    """
    Parses release information and values, then parses them together into a dictionary
    with the specified release, namespace, repository, and values
    Arguments:
    release: The name of the release to import. No default.
    namespace: The namespace of the release to import. No default.
    repository: The repository the chart is from. No Default

    Returns:
    Dictionary of realease information
    """
    release_info = list_release(release, namespace)
    release_values = get_values(release, namespace)

    output = {
        release: {
            'chart': "-".join(release_info.get('chart', '').split('-')[0:-1]),
            'repository': repository,
            'version': release_info.get('chart', '').split('-')[-1],
            'namespace': namespace,
            'values': release_values,
        }
    }

    return output
