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
				Repositories: []Repository{
					{
						Name: "git-repo-test",
						Git:  "https://github.com/FairwindsOps/charts",
						Path: "stable",
					},

					{
						Name: "helm-repo",
						URL:  "https://ahelmrepo.example.com",
					},
					{
						Name: "gitrelease-git-repository",
						Git:  "giturl",
						Path: "gitpath",
					},
				},
				Releases: []Release{
					{
						Name:       "basic",
						Chart:      "somechart",
						Version:    "2.0.0",
						Repository: "helm-repo",
						Values: map[string]interface{}{
							"dummyvalue": false,
						},
					},
					{
						Name:       "gitrelease",
						Chart:      "gitchart",
						Version:    "main",
						Repository: "gitrelease-git-repository",
						Values:     nil,
					},
					{
						Name:       "standard",
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
