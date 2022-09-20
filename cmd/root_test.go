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

package cmd

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestGetCourseFilePath(t *testing.T) {
	tests := []struct {
		name string
		path []string
		want string
	}{
		{
			name: "empty path, expect default",
			path: []string{},
			want: "course.yaml",
		},
		{
			name: "single course.yaml specified, expect mirror",
			path: []string{"testdata/course.yaml"},
			want: "testdata/course.yaml",
		},
		{
			name: "multiple course.yaml specified, expect first",
			path: []string{"testdata/course.yaml", "second_course.yaml"},
			want: "testdata/course.yaml",
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			courseFilePath := getCourseFilePath(tt.path) // get course file path
			assert.Equal(t, tt.want, courseFilePath)     // compare wanted vs result
		})
	}
}
