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

import sys
import logging
import traceback

from .config import Config
from kubernetes import client, config


class NamespaceManager(object):

    def __init__(self, namespace_name, namespace_management) -> None:
        """ Manages a namespace for the chart
        Accepts:
        - namespace: Which may be a string or a dictionary
        """
        self._namespace_name = namespace_name
        self._metadata = namespace_management.get('metadata', {})
        self._overwrite = namespace_management.get(
            'settings',
            {}
        ).get(
            'overwrite',
            False
        )
        self.__load_config()
        self.config = Config()

    @property
    def namespace_name(self) -> str:
        """ Name of the namespace we are managing """
        return self._namespace_name

    @property
    def namespace(self) -> str:
        """ Namespace object we are managing 
        https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1Namespace.md"""
        return self._namespace

    @property
    def metadata(self) -> dict:
        """ List of metadata settings parsed from the
        from the chart and course """
        return self._metadata

    @property
    def overwrite(self) -> bool:
        """ List of metadata settings parsed from the
        from the chart and course """
        return self._overwrite

    def __load_config(self):
        """ Protected method to load kubernetes config"""
        try:
            config.load_kube_config()
            self.v1client = client.CoreV1Api()
        except Exception as e:
            logging.error('Unable to load kubernetes configuration')
            logging.debug(traceback.format_exc())
            raise e

    def create_and_manage(self):
        """ Create namespace and patch metadata """
        if self.config.dryrun:
            logging.warning(
                "Namespace not created or patched due to "
                "--dry-run: {}".format(self.namespace_name)
            )

            return
        self._namespace = self.create()
        self.patch_metadata()

    def patch_metadata(self):
        """ Patch namespace with metadata respecting overwrite setting.
        Returns True on success
        Raises error on failure
        """
        if self.overwrite:
            patch_metadata = self.metadata
            logging.info("Overwriting Namespace '{}' Metadata".format(self.namespace_name))
        else:
            annotations = {}
            for annotation_name, annotation_value in self.metadata.get('annotations', {}).items():
                try:
                    current_annotation_value = self.namespace.metadata.annotations[annotation_name]
                    if current_annotation_value != annotation_value:
                        logging.info("Not Overwriting Metadata Annotation '{}' in Namespace '{}'".format(annotation_name,self.namespace_name))
                except (TypeError, KeyError):
                    annotations[annotation_name] = annotation_value

            labels = {}
            for label_name, label_value in self.metadata.get('labels', {}).items():
                try:
                    current_label_value = self.namespace.metadata.labels[label_name]
                    if current_label_value != annotation_value:
                        logging.info("Not Overwriting Metadata Label '{}' in Namespace '{}'".format(annotation_name,self.namespace_name))
                except (TypeError, KeyError):
                    labels[label_name] = label_value

            patch_metadata = {'annotations': annotations, 'labels': labels}
        logging.debug("Patch Metadata: {}".format(patch_metadata))
        patch = {'metadata': patch_metadata}
        res = self.v1client.patch_namespace(self.namespace_name, patch)

    def create(self):
        """ Create a namespace in the configured kubernetes cluster if it does not already exist

        Arguments:
        None

        Returns Namespace
        Raises error in case of failure

        """
        _namespaces = [namespace for namespace in self.cluster_namespaces if namespace.metadata.name == self.namespace_name]

        if _namespaces == []:
            logging.info('Namespace {} not found. Creating it now.'.format(self.namespace_name))
            try:
                return self.v1client.create_namespace(
                    client.V1Namespace(
                        metadata=client.V1ObjectMeta(name=self.namespace_name)
                    )
                )

            except Exception as e:
                logging.error("Unable to create namespace in cluster! {}".format(e))
                logging.debug(traceback.format_exc())
                raise e
        else:
            return _namespaces[0]

    @property
    def cluster_namespaces(self) -> list:
        """ Lists namespaces in the configured kubernetes cluster.
        No arguments
        Returns list of namespace objects
        """
        try:
            namespaces = self.v1client.list_namespace()
            return [namespace for namespace in namespaces.items]
        except Exception as e:
            logging.error("Unable to get namespaces in cluster! {}".format(e))
            logging.debug(traceback.format_exc())
            raise e
