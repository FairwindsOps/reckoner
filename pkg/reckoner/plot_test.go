// Copyright 2022 Fairwinds
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

const (
	baseDir        = "path/to/chart"
	namespace      = "basic-ns"
	version        = "v0.0.0"
	valuesFile     = "a-values-file.yaml"
	helmChart      = "helmchart"
	helmRelease    = "basic-release"
	helmRepository = "helmrepo"
)

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
			baseDir: baseDir,
			args: args{
				command: "template",
				release: course.Release{
					Name:       helmRelease,
					Namespace:  namespace,
					Chart:      helmChart,
					Version:    version,
					Repository: helmRepository,
					Files: []string{
						valuesFile,
					},
				},
			},
			want: []string{
				"template",
				helmRelease,
				helmRepository + "/" + helmChart,
				"--values=" + baseDir + "/" + valuesFile,
				"--namespace=" + namespace,
				"--version=" + version,
			},
			wantErr: false,
		},
		{
			name:    "basic upgrade",
			baseDir: baseDir,
			args: args{
				command: "upgrade",
				release: course.Release{
					Name:       helmRelease,
					Namespace:  namespace,
					Chart:      helmChart,
					Version:    version,
					Repository: helmRepository,
					Files: []string{
						valuesFile,
					},
				},
			},
			want: []string{
				"upgrade",
				"--install",
				helmRelease,
				helmRepository + "/" + helmChart,
				"--values=" + baseDir + "/" + valuesFile,
				"--namespace=" + namespace,
				"--version=" + version,
			},
			wantErr: false,
		},
		{
			name:    "additional args",
			baseDir: baseDir,
			args: args{
				command: "upgrade",
				release: course.Release{
					Name:       helmRelease,
					Namespace:  namespace,
					Chart:      helmChart,
					Version:    version,
					Repository: helmRepository,
					Files: []string{
						valuesFile,
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
				helmRelease,
				helmRepository + "/" + helmChart,
				"--values=" + baseDir + "/" + valuesFile,
				"--namespace=" + namespace,
				"--version=" + version,
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
