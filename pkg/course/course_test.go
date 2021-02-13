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

package course

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestConvertV1toV2(t *testing.T) {

	tests := []struct {
		name     string
		fileName string
		want     *FileV2
		wantErr  bool
	}{
		{

			name:     "file not exist",
			fileName: "thisfileshouldneverexist",
			wantErr:  true,
		},
		{
			name:     "unmarshal error",
			fileName: "testdata/unmarshalerror.yaml",
			wantErr:  true,
		},
		{
			name:     "really basic",
			fileName: "testdata/convert1.yaml",
			wantErr:  false,
			want: &FileV2{
				SchemaVersion:     "v2",
				DefaultNamespace:  "namespace",
				DefaultRepository: "stable",
				Context:           "farglebargle",
				Repositories: RepositoryList{
					"git-repo-test": {
						Git:  "https://github.com/FairwindsOps/charts",
						Path: "stable",
					},
					"helm-repo": {
						URL: "https://ahelmrepo.example.com",
					},
					"gitrelease-git-repository": {
						Git:  "giturl",
						Path: "gitpath",
					},
				},
				Releases: ReleaseList{
					"basic": {
						Chart:      "somechart",
						Version:    "2.0.0",
						Repository: "helm-repo",
						Values: map[string]interface{}{
							"dummyvalue": false,
						},
					},
					"gitrelease": {
						Chart:      "gitchart",
						Version:    "main",
						Repository: "gitrelease-git-repository",
						Values:     nil,
					},
					"standard": {
						Chart:      "basic",
						Repository: "helm-repo",
						Values:     nil,
					},
				},
			},
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := ConvertV1toV2(tt.fileName)
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.EqualValues(t, tt.want, got)
			}
		})
	}
}

func TestFileV2_populateDefaultNamespace(t *testing.T) {
	type fields struct {
		DefaultNamespace string
		Releases         ReleaseList
	}
	tests := []struct {
		name   string
		fields fields
		want   ReleaseList
	}{
		{
			name: "basic test",
			fields: fields{
				DefaultNamespace: "default-ns",
				Releases: map[string]Release{
					"first-release": {
						Chart: "farglebargle",
					},
				},
			},
			want: map[string]Release{
				"first-release": {
					Chart:     "farglebargle",
					Namespace: "default-ns",
				},
			},
		},
		{
			name: "no default namespace",
			fields: fields{
				DefaultNamespace: "",
				Releases: map[string]Release{
					"first-release": {
						Chart: "farglebargle",
					},
				},
			},
			want: map[string]Release{
				"first-release": {
					Chart: "farglebargle",
				},
			},
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			f := &FileV2{
				DefaultNamespace: tt.fields.DefaultNamespace,
				Releases:         tt.fields.Releases,
			}
			f.populateDefaultNamespace()
			assert.EqualValues(t, tt.want, f.Releases)
		})
	}
}

func TestFileV2_populateDefaultRepository(t *testing.T) {
	type fields struct {
		DefaultRepository string
		Releases          ReleaseList
	}
	tests := []struct {
		name   string
		fields fields
		want   ReleaseList
	}{
		{
			name: "basic test",
			fields: fields{
				DefaultRepository: "default-repo",
				Releases: map[string]Release{
					"first-release": {
						Chart: "farglebargle",
					},
				},
			},
			want: map[string]Release{
				"first-release": {
					Chart:      "farglebargle",
					Repository: "default-repo",
				},
			},
		},
		{
			name: "no default set",
			fields: fields{
				DefaultRepository: "",
				Releases: map[string]Release{
					"first-release": {
						Chart: "farglebargle",
					},
				},
			},
			want: map[string]Release{
				"first-release": {
					Chart: "farglebargle",
				},
			},
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			f := &FileV2{
				DefaultRepository: tt.fields.DefaultRepository,
				Releases:          tt.fields.Releases,
			}
			f.populateDefaultRepository()
			assert.EqualValues(t, tt.want, f.Releases)
		})
	}
}
