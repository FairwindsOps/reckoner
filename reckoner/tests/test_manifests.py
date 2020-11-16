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

import unittest
from unittest import mock
from reckoner.yaml.handler import Handler as yaml_handler
from reckoner.manifests import Manifest, Manifests, diff

class TestManifests(unittest.TestCase):
    def setUp(self):
        with open('./reckoner/tests/files/templates.yaml') as templates:
            self.manifests = Manifests(templates.read())

    def test_manifest_load_error(self):
        with self.assertRaises(Exception):
            Manifests("---\njunk: - information: that | does , not play")

    def test_manifests_loaded(self):

        # All member of the all_manifest list are of type Manifest
        for manifest in self.manifests.all_manifests:
            self.assertIsInstance(manifest, (Manifest))

        # There number of documents in the test file should equal the number of manifets
        self.assertEqual(len(self.manifests.all_manifests), 6)

        # Prior to modification, all_manifests == filtered_manifest
        self.assertEqual(self.manifests.all_manifests, self.manifests.filtered_manifests)

    def test_filter_by_annotation(self):

        # removes any manifests with this annotation name
        self.manifests.filter_by_annotation_name('helm.sh/hook')

        for manifest in self.manifests.filtered_manifests:
            annotation_keys = [key for key in manifest.annotations]
            self.assertNotIn('"helm.sh/hook"', annotation_keys)

        self.assertEqual(len(self.manifests.filtered_manifests), 5)

    def test_find_congruent_manifest(self):
        with open('./reckoner/tests/files/service.yaml') as f:
            document = f.read()
        service_manifest = Manifest(yaml_handler.load(document))

        print(service_manifest.kind)

        found = self.manifests.find_congruent_manifest(service_manifest)
        print(found)
        self.assertIsInstance(found, (Manifest))
        self.assertEqual(found.kind, 'Service')
        self.assertEqual(found.name, 'reckoner-test-service')
        self.assertEqual(found.annotations, {})

    def test_filter_by_kind(self):
        self.manifests.filter_by_kind('Pod')
        self.manifests.filter_by_kind('DaemonSet')
        self.manifests.filter_by_kind('List')
        self.assertEqual(len(self.manifests.filtered_manifests), 2)
        self.assertEqual(self.manifests.filtered_manifests[0].kind, 'ConfigMap')


class TestManifest(unittest.TestCase):
    def setUp(self):
        with open('./reckoner/tests/files/service.yaml') as f:
            self.document = f.read()
        self.service_manifest = Manifest(yaml_handler.load(self.document))

    def test_kind_and_name(self):
        self.assertEqual(self.service_manifest.name, 'reckoner-test-service')
        self.assertEqual(self.service_manifest.kind, 'Service')

    def test_str_method(self):
        self.assertEqual(
            yaml_handler.load(str(self.service_manifest)),
            yaml_handler.load(self.document)
        )

    def test_diff_types(self):
        self.service_manifest.diff(Manifest(yaml_handler.load(self.document)), difftype='unified')
        self.service_manifest.diff(Manifest(yaml_handler.load(self.document)), difftype='context')
        with self.assertRaises((TypeError)):
            self.service_manifest.diff(Manifest(yaml_handler.load(self.document)), difftype='wrong')


class TestDiff(unittest.TestCase):

    def test_no_difference(self):
        with open('./reckoner/tests/files/templates.yaml') as templates:
            t1 = templates.read()

        with open('./reckoner/tests/files/templates.yaml') as templates:
            t2 = templates.read()

        self.assertEqual(diff(t1, t2), '')

    def test_with_name_difference(self):
        with open('./reckoner/tests/files/templates.yaml') as templates:
            t1 = templates.read()

        with open('./reckoner/tests/files/templates2.yaml') as templates:
            t2 = templates.read()
        self.maxDiff = None
        template_diff = diff(t1, t2)

        # The change makes a manifests get removed and one with a new name get created
        self.assertTrue(r'DaemonSet: "a2-aws-iam-authenticator-test2" does not exist and will be added' in template_diff)
        self.assertTrue(r'DaemonSet: "a2-aws-iam-authenticator" exists but will be removed' in template_diff)
        self.assertFalse(r'helm.sh/hook' in template_diff)

    def test_with_annotation_difference(self):
        with open('./reckoner/tests/files/templates.yaml') as templates:
            t1 = templates.read()

        with open('./reckoner/tests/files/templates3.yaml') as templates:
            t2 = templates.read()
        self.maxDiff = None
        template_diff = diff(t1, t2)

        self.assertTrue(r'-    k8s-app: aws-iam-authenticator' in template_diff)
        self.assertTrue(r'+    k8s-app: aws-iam-authenticator-test' in template_diff)
        self.assertFalse(r'helm.sh/hook' in template_diff)
