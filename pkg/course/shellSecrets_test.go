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

func Test_executor_Get(t *testing.T) {
	type fields struct {
		Executable string
		Args       []string
	}
	type args struct {
		key string
	}
	tests := []struct {
		name    string
		fields  fields
		args    args
		want    string
		wantErr bool
	}{
		{
			name: "test",
			fields: fields{
				Executable: "echo",
				Args:       []string{"-n", "hello"},
			},
			args: args{
				key: "test",
			},
			want:    "hello",
			wantErr: false,
		},
		{
			name: "error",
			fields: fields{
				Executable: "exit",
				Args:       []string{"1"},
			},
			args: args{
				key: "test",
			},
			want:    "hello",
			wantErr: true,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			s := executor{
				Executable: tt.fields.Executable,
				Args:       tt.fields.Args,
			}
			got, err := s.Get(tt.args.key)
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.EqualValues(t, tt.want, got)
			}
		})
	}
}

func Test_newShellExecutor(t *testing.T) {
	type args struct {
		script []string
	}
	tests := []struct {
		name    string
		args    args
		want    *executor
		wantErr bool
	}{
		{
			name: "basic",
			args: args{[]string{"echo", "-n", "hello"}},
			want: &executor{
				Executable: "/bin/echo",
				Args:       []string{"-n", "hello"},
			},
			wantErr: false,
		},
		{
			name: "no args",
			args: args{[]string{"echo"}},
			want: &executor{
				Executable: "/bin/echo",
				Args:       []string{},
			},
			wantErr: false,
		},
		{
			name:    "no args",
			args:    args{[]string{"farglebargleshouldreallynotbeanexecutable"}},
			wantErr: true,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := newShellExecutor(tt.args.script)
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.EqualValues(t, tt.want, got)
			}
		})
	}
}
