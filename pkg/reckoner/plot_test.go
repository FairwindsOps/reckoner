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
	"os"
	"testing"

	"github.com/fairwindsops/reckoner/pkg/course"
	"github.com/stretchr/testify/assert"
)

const baseDirPlaceholder = "path/to/chart"

func Test_buildHelmArgs(t *testing.T) {
	type args struct {
		command        string
		release        course.Release
		additionalArgs []string
	}
	tests := []struct {
		name    string
		baseDir string
		args    args
		want    []string
		wantErr bool
	}{
		{
			name:    "basic template",
			baseDir: baseDirPlaceholder,
			args: args{
				command: "template",
				release: course.Release{
					Name:       "basic-release",
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
				"--values=path/to/chart/a-values-file.yaml",
				"--namespace=basic-ns",
				"--version=v0.0.0",
			},
			wantErr: false,
		},
		{
			name:    "basic upgrade",
			baseDir: baseDirPlaceholder,
			args: args{
				command: "upgrade",
				release: course.Release{
					Name:       "basic-release",
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
				"--values=path/to/chart/a-values-file.yaml",
				"--namespace=basic-ns",
				"--version=v0.0.0",
			},
			wantErr: false,
		},
		{
			name:    "additional args",
			baseDir: baseDirPlaceholder,
			args: args{
				command: "upgrade",
				release: course.Release{
					Name:       "basic-release",
					Namespace:  "basic-ns",
					Chart:      "helmchart",
					Version:    "v0.0.0",
					Repository: "helmrepo",
					Files: []string{
						"a-values-file.yaml",
					},
				},
				additionalArgs: []string{
					"--atomic",
				},
			},
			want: []string{
				"upgrade",
				"--install",
				"--atomic",
				"basic-release",
				"helmrepo/helmchart",
				"--values=path/to/chart/a-values-file.yaml",
				"--namespace=basic-ns",
				"--version=v0.0.0",
			},
			wantErr: false,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, _, err := buildHelmArgs(tt.args.command, tt.baseDir, tt.args.release, tt.args.additionalArgs)
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.EqualValues(t, tt.want, got)
			}
		})
	}
}

func Test_makeTempValuesFile(t *testing.T) {
	tests := []struct {
		name    string
		values  map[string]interface{}
		want    string
		wantErr bool
	}{
		{
			name: "basic",
			values: map[string]interface{}{
				"foo": "bar",
			},
			want:    "foo: bar\n",
			wantErr: false,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := makeTempValuesFile(tt.values)
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				valuesFile, err := os.ReadFile(got.Name())
				assert.NoError(t, err)
				assert.EqualValues(t, tt.want, string(valuesFile))
			}
			os.Remove(got.Name())
		})
	}
}
