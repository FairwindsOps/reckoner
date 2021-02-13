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

	"github.com/fairwindsops/reckoner/pkg/course"
	"github.com/stretchr/testify/assert"
)

func Test_buildHelmArgs(t *testing.T) {
	type args struct {
		releaseName string
		command     string
		release     course.Release
	}
	tests := []struct {
		name    string
		args    args
		want    []string
		wantErr bool
	}{
		{
			name: "basic template",
			args: args{
				releaseName: "basic-release",
				command:     "template",
				release: course.Release{
					Namespace:  "basic-ns",
					Chart:      "helmchart",
					Version:    "v0.0.0",
					Repository: "helmrepo",
					Files: []string{
						"a-values-file.yaml",
					},
				},
			},
			want: []string{
				"template",
				"basic-release",
				"helmrepo/helmchart",
				"--values=a-values-file.yaml",
				"--namespace=basic-ns",
				"--version=v0.0.0",
			},
			wantErr: false,
		},
		{
			name: "basic upgrade",
			args: args{
				releaseName: "basic-release",
				command:     "upgrade",
				release: course.Release{
					Namespace:  "basic-ns",
					Chart:      "helmchart",
					Version:    "v0.0.0",
					Repository: "helmrepo",
					Files: []string{
						"a-values-file.yaml",
					},
				},
			},
			want: []string{
				"upgrade",
				"--install",
				"basic-release",
				"helmrepo/helmchart",
				"--values=a-values-file.yaml",
				"--namespace=basic-ns",
				"--version=v0.0.0",
			},
			wantErr: false,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, _, err := buildHelmArgs(tt.args.releaseName, tt.args.command, tt.args.release)
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.EqualValues(t, tt.want, got)
			}
		})
	}
}
