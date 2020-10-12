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

import os
import re
import difflib
import logging
import traceback

from .yaml.handler import Handler as yaml_handler


class Manifest(object):
    def __init__(self, document: dict) -> None:
        self.document = document

    @property
    def metadata(self):
        return self.document.get('metadata') or {}

    @property
    def annotations(self):
        return self.metadata.get('annotations') or {}

    @property
    def name(self):
        return self.metadata.get('name')

    @property
    def kind(self):
        return self.document.get('kind')

    @property
    def source(self):
        try:
            return self.document.ca.comment[1][0].value.replace('# Source:', '').strip()
        except Exception as e:
            logging.error(e)
            logging.debug(traceback.format_exc)
            logging.warn(
                f'Unable to determine the source of '
                '{self.kind} "{self.name}". This may '
                'yield unexpected results!')

    def __str__(self):
        return yaml_handler.dump(self.document)

    def __eq__(self, other):
        if not isinstance(other, (Manifest)):
            raise TypeError(f"Cannot compare {type(other)} to Manifest()")

        return other.document == self.document

    def __bool__(self):
        return bool(self.document)

    def diff(self, other, difftype="unified"):
        """
        Returns a list of diff lines from the diff between this Manifest
        instance and the supplied Manifest instance.

        difftype may be "unified" [DEFAULT] or "context"
        """

        if difftype.lower() == "unified":
            differ = difflib.unified_diff
        elif difftype.lower() == "context":
            differ = difflib.context_diff
        else:
            raise TypeError('difftype argument may only "unified" or "context"')

        return list(
            differ(
                str(self).splitlines(),
                str(other).splitlines(),
            )
        )


class Manifests(object):
    """
    Provides a way to filter yaml documents, based on
    certain characteristics, from a string or stream containing
    valid yaml manifests
    """

    def __init__(self, documents: str) -> None:
        """
        Parameters:
        -----------
        - manifest: String containing
        """
        try:
            self.all_manifests = [Manifest(document) for document in yaml_handler.load_all(documents.strip()) if document]
        except Exception as e:
            logging.error("Error loading manifest")
            logging.error(e)
            logging.debug(traceback.format_exc())
            raise e
        self.filtered_manifests = self.all_manifests

    def filter_by_annotation_name(self, filter_annotation_key: str) -> None:
        """
        Removes manifests from the instances filtered_manifests attribute
        if they have an annotation that matches the 'filter_annotation_key'
        parameter
        """

        _new_filtered_manifests = []
        for manifest in self.filtered_manifests:
            if manifest.annotations == {}:
                logging.debug(f"manifest {manifest.kind} named {manifest.name} has no annotations to filter on")
                _new_filtered_manifests.append(manifest)
            else:
                if filter_annotation_key not in [manifest_annotation_key for manifest_annotation_key in manifest.annotations]:
                    _new_filtered_manifests.append(manifest)
                else:
                    logging.debug(f"Filtering {manifest.kind} named {manifest.name} for {filter_annotation_key} ")

        self.filtered_manifests = _new_filtered_manifests

    def filter_by_kind(self, kind: str) -> None:
        """
        Removes manifests from the instances filtered_manifests attribute
        if they are of the kind specified in the 'kind' parameter
        """
        _new_filtered_manifests = []
        for manifest in self.filtered_manifests:
            if manifest.kind != kind:
                _new_filtered_manifests.append(manifest)

        self.filtered_manifests = _new_filtered_manifests

    def find_congruent_manifest(self, manifest: Manifest) -> Manifest:
        """
        Given a manifest, returns the most matching manifest
        in this list of filtered_manifests using source, name
        or kind
        """
        if isinstance(manifest, (Manifest)):
            logging.debug(f"Looking for {manifest.kind} name {manifest.name} with source {manifest.source}")
            if manifest.kind == 'List':
                return self.__find_by_kind_and_source(manifest.kind, manifest.source)
            return self.__find_by_kind_and_name(manifest.kind, manifest.name)

        raise TypeError("'manifest' argument must be of type Manifest()")

    def __find_by_kind_and_name(self, kind: str, name: str) -> Manifest:
        """
        Returns the manifest from the filtered manifests
        that matches the paramters kind and name, as a string
        """
        try:
            return [
                manifest
                for manifest
                in self.filtered_manifests
                if manifest.kind == kind
                and manifest.name == name
            ][0]
        except IndexError:
            pass

        return Manifest({})

    def __find_by_kind_and_source(self, kind: str, source: str) -> Manifest:
        """
        Returns the manifest from the filtered manifests
        where the source matches the paramters source as a string
        """
        try:
            return [
                manifest
                for manifest
                in self.filtered_manifests
                if manifest.source == source
                and manifest.kind == kind
            ][0]
        except IndexError:
            pass

        return Manifest({})

    def __iter__(self):
        for manifest in self.filtered_manifests:
            yield manifest


def diff(current: str, new: str, show_hooks: bool = False):
    current_manifests = Manifests(current)
    new_manifests = Manifests(new)

    for _manifest in [current_manifests, new_manifests]:
        if show_hooks is False:
            _manifest.filter_by_annotation_name('helm.sh/hook')

    output_lines = []
    for new_manifest in new_manifests:
        diff_lines = []
        matching_existing_manifest = current_manifests.find_congruent_manifest(new_manifest)

        manifest_separator_message = f'{new_manifest.kind}: "{new_manifest.name}"'
        if not matching_existing_manifest:
            manifest_separator_message += " does not exist and will be added "
        manifest_separator_lines = ['', manifest_separator_message]

        diff_lines = matching_existing_manifest.diff(new_manifest)
        if diff_lines:
            output_lines += manifest_separator_lines
            output_lines += diff_lines

    for current_manifest in current_manifests:
        matching_new_manifest = new_manifests.find_congruent_manifest(current_manifest)
        if not matching_new_manifest:
            output_lines += ['', '', f'{current_manifest.kind}: "{current_manifest.name}" exists but will be removed', '']
            output_lines += current_manifest.diff(matching_new_manifest)

    return "\n".join(output_lines)
