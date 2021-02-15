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

	"github.com/stretchr/testify/assert"
)

func TestValidateArgs(t *testing.T) {
	type args struct {
		runAll  bool
		onlyRun []string
		args    []string
	}
	tests := []struct {
		name    string
		args    args
		want    string
		wantErr bool
	}{
		{
			name:    "empty args",
			args:    args{},
			want:    "",
			wantErr: true,
		},
		{
			name: "course.yaml does not exist",
			args: args{
				args:   []string{"course.yaml"},
				runAll: true,
			},
			want:    "",
			wantErr: true,
		},
		{
			name: "course.yaml not exist, but no -a or -o passed",
			args: args{
				args: []string{"testdata/course.yaml"},
			},
			want:    "",
			wantErr: true,
		},
		{
			name: "course.yaml not exist, but no -a or -o passed",
			args: args{
				args: []string{"testdata/course.yaml"},
			},
			want:    "",
			wantErr: true,
		},
		{
			name: "course.yaml exists, Only one of runAll or onlyRun can be set",
			args: args{
				args:    []string{"testdata/course.yaml"},
				runAll:  true,
				onlyRun: []string{"rbac-manager"},
			},
			wantErr: true,
		},
		{
			name: "course.yaml exists, pass onlyrun with success",
			args: args{
				args:    []string{"testdata/course.yaml"},
				runAll:  false,
				onlyRun: []string{"rbac-manager"},
			},
			want:    "testdata/course.yaml",
			wantErr: false,
		},
		{
			name: "course.yaml exists, pass runall with success",
			args: args{
				args:   []string{"testdata/course.yaml"},
				runAll: true,
			},
			want:    "testdata/course.yaml",
			wantErr: false,
		},
		{
			name: "course.yaml exists, length of args = 2",
			args: args{
				args:    []string{"testdata/course.yaml", "course.yml"},
				runAll:  false,
				onlyRun: []string{"rbac-manager"},
			},
			wantErr: true,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := ValidateArgs(tt.args.runAll, tt.args.onlyRun, tt.args.args)
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.Equal(t, tt.want, got)
			}
		})
	}
}
