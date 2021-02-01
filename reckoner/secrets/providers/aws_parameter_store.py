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

import boto3
import logging
import traceback

from .base import SecretProvider

logger = logging.getLogger(__name__)


class AWSParameterStore(SecretProvider):
    """
    Secret Provider for AWS SSM Parameter Store secrets
    Required Arguments:
    `parameter_name`: The name of the Parameter Store Value
    Optional Arguments:
    `region`: Use when the Parameter is not in the AWS configured region

    """

    def __init__(self, parameter_name, region=None):
        self.ssm_parameter_name = parameter_name
        self.ssm_client_extra_args = {}
        if region is not None:
            self.ssm_client_extra_args['region_name'] = region

    def __get_client(self):
        try:
            return boto3.client('ssm', **self.ssm_client_extra_args)
        except Exception as e:
            logger.error(f"Error with AWS Configuration")
            logger.debug(traceback.format_exc())
            raise e

    def get_value(self):

        client = self.__get_client()
        try:
            return client.get_parameter(
                Name=self.ssm_parameter_name,
                WithDecryption=True
            )['Parameter']['Value']
        except Exception as e:
            logger.error(f"Error retrieving secret value")
            logger.debug(traceback.format_exc())
            raise e
