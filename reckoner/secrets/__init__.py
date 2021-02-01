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

from .providers import *


class Secret(object):

    """
    Secret:

    Required Arguments:
    `name`: The name of the secret. Must match the target inline variable. For example
    if your `values` has a template variable `${PASSWORD}` the name must be `PASSWORD`

    `backend`: Defines what secret provider to use to retrieve the secrets value.
    `backend` must be one of the Secret.ALLOWED_BACKENDS

    Properties:
    `name`: The name of the sercret to be used for templating
    `value`: The retrieved value from the provider

    """
    ALLOWED_BACKENDS = ['AWSParameterStore', 'ShellExecutor']

    def __init__(self, name, backend, *args, **kwargs) -> None:
        self.__kwargs = kwargs
        if backend not in self.ALLOWED_BACKENDS:
            raise TypeError(
                f"Provided Backend: '{backend}' is not supported."
                "Must be one of {self.ALLOWED_BACKENDS}"
            )

        self._name = name
        self._backend = backend

    def __str__(self) -> str:
        return self.name

    @property
    def name(self) -> str:
        """Returns the name of the secret"""
        return self._name

    @property
    def provider(self):
        """
        Gets provider class from loaded modules based on
        `backend`, and returns it
        """
        if not hasattr(self, "_provider"):
            self._provider = globals()[self._backend]
        return self._provider


    @property
    def value(self) -> str:
        "Returns the value of the secret from the secret provider"
        if not hasattr(self, "_value"):
            self._value = self.provider(**self.__kwargs).get_value()
        return self._value
