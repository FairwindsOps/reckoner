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

from .helm.client import get_helm_client
from .config import Config
from .exception import ReckonerException
from .yaml.handler import Handler as yaml


def get_values(release, namespace):
    helm_client = get_helm_client(helm_arguments=Config().helm_args)
    response = helm_client.get_values(
        [f'--namespace={namespace}', release]
    )
    if response.exit_code:
        raise ReckonerException(f'Error getting values: {response.stderr}')

    return json.loads(response.stdout)


def list_release(release, namespace):
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


def draft_release(release, namespace, repository):
    release_info = list_release(release, namespace)
    release_values = get_values(release, namespace)

    output = {
        release: {
            'chart': release_info.get('chart', '').split('-')[0],
            'repository': repository,
            'version': release_info.get('chart', '').split('-')[1],
            'namespace': namespace,
            'values': release_values,
        }
    }


    print(yaml.dump(output))
