// Copyright 2020 Fairwinds
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License

package reckoner

import (
	"testing"

	"github.com/fatih/color"
	"github.com/stretchr/testify/assert"
)

var (
	serviceAccountTemplate = `apiVersion: v1
kind: ServiceAccount
metadata:
  name: example-controller
  labels:
	app.kubernetes.io/name: example
	helm.sh/chart: example-1.0.0
	app.kubernetes.io/instance: example
	app.kubernetes.io/managed-by: Helm
	app.kubernetes.io/component: controller
`
	modifiedServiceAccountTemplate = `apiVersion: v1
kind: ServiceAccount
metadata:
  name: example-controller-1
  labels:
	app.kubernetes.io/name: example
	helm.sh/chart: example-1.0.0
	app.kubernetes.io/instance: example
	app.kubernetes.io/managed-by: Helm
	app.kubernetes.io/component: controller
`
	clusterRoleTemplate = `apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: example-controller
  labels:
	app.kubernetes.io/name: example
	helm.sh/chart: example-1.0.0
	app.kubernetes.io/instance: example
	app.kubernetes.io/managed-by: Helm
	app.kubernetes.io/component: controller
rules:
  - apiGroups:
	  - 'apps'
	resources:
	  - '*'
	verbs:
	  - 'get'
	  - 'list'
	  - 'watch'
  - apiGroups:
	  - ''
	resources:
	  - 'namespaces'
	  - 'pods'
	verbs:
	  - 'get'
	  - 'list'
	  - 'watch'
  - apiGroups:
	  - 'autoscaling.k8s.io'
	resources:
	  - 'verticalpodautoscalers'
	verbs:
	  - 'get'
	  - 'list'
	  - 'create'
	  - 'delete'
	  - 'update'
`
	testGetManifestSlice = []Manifest{
		{
			Source: "example/templates/controller-serviceaccount.yaml",
			Kind:   "ServiceAccount",
			Metadata: Metadata{
				Name: "example-controller",
			},
			Content: serviceAccountTemplate,
		},
		{
			Source: "example/templates/controller-clusterrole.yaml",
			Kind:   "ClusterRole",
			Metadata: Metadata{
				Name: "example-controller",
			},
			Content: clusterRoleTemplate,
		},
	}
	testTemplateSlice = []Manifest{
		{
			Source: "example/templates/controller-serviceaccount.yaml",
			Kind:   "ServiceAccount",
			Metadata: Metadata{
				Name: "example-controller",
			},
			Content: serviceAccountTemplate,
		},
		{
			Source: "example/templates/controller-clusterrole.yaml",
			Kind:   "ClusterRole",
			Metadata: Metadata{
				Name: "example-controller",
			},
			Content: clusterRoleTemplate,
		},
	}
	testTemplateSliceModified = []Manifest{
		{
			Source: "example/templates/controller-serviceaccount.yaml",
			Kind:   "ServiceAccount",
			Metadata: Metadata{
				Name: "example-controller",
			},
			Content: modifiedServiceAccountTemplate,
		},
		{
			Source: "example/templates/controller-clusterrole.yaml",
			Kind:   "ClusterRole",
			Metadata: Metadata{
				Name: "example-controller",
			},
			Content: clusterRoleTemplate,
		},
	}
	wantedManifestDiffSlice = []ManifestDiff{
		{
			ReleaseName: "example",
			Kind:        "ServiceAccount",
			Name:        "example-controller",
			Source:      "example/templates/controller-serviceaccount.yaml",
			Diff:        "",
			NewFile:     false,
		},
		{
			ReleaseName: "example",
			Kind:        "ClusterRole",
			Name:        "example-controller",
			Source:      "example/templates/controller-clusterrole.yaml",
			Diff:        "",
			NewFile:     false,
		},
	}
	wantedManifestDiffSliceModified = []ManifestDiff{
		{
			ReleaseName: "example",
			Kind:        "ServiceAccount",
			Name:        "example-controller",
			Source:      "example/templates/controller-serviceaccount.yaml",
			Diff:        "\nkind: ServiceAccount\nmetadata:\n- name: example-controller\n+ name: example-controller-1\n  labels:\n\tapp.kubernetes.io/name: example\n\thelm.sh/chart: example-1.0.0\n\tapp.kubernetes.io/instance: example\n\n",
			NewFile:     false,
		},
		{
			ReleaseName: "example",
			Kind:        "ClusterRole",
			Name:        "example-controller",
			Source:      "example/templates/controller-clusterrole.yaml",
			Diff:        "",
			NewFile:     false,
		},
	}
)

func Test_populateDiffs(t *testing.T) {
	tests := []struct {
		name        string
		releaseName string
		mSlice      []Manifest
		tSlice      []Manifest
		want        []ManifestDiff
		wantErr     bool
	}{
		{
			name:        "populateDiffs_no_diff",
			releaseName: "example",
			mSlice:      testGetManifestSlice,
			tSlice:      testTemplateSlice,
			want:        wantedManifestDiffSlice,
			wantErr:     false,
		},
		{
			name:        "populateDiffs_diff",
			releaseName: "example",
			mSlice:      testGetManifestSlice,
			tSlice:      testTemplateSliceModified,
			want:        wantedManifestDiffSliceModified,
			wantErr:     false,
		},
	}
	for _, tt := range tests {
		color.NoColor = true // disable color output so that we can more easily compare output strings in Diff
		t.Run(tt.name, func(t *testing.T) {
			got, err := populateDiffs(tt.releaseName, tt.mSlice, tt.tSlice)
			if (err != nil) != tt.wantErr {
				t.Errorf("populateDiffs() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			assert.Equal(t, tt.want, got)
		})
	}
}
