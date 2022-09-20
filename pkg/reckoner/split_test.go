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
	"testing"

	"github.com/stretchr/testify/assert"
)

func Test_splitYAML(t *testing.T) {
	tests := []struct {
		name             string
		yamlFile         []byte
		want             [][]byte
		wantNumberOfDocs int
		wantErr          bool
	}{
		{
			name:     "one_document",
			yamlFile: []byte("---\nfield: \"value\"\n"),
			want: [][]byte{
				[]byte("field: value"),
			},
			wantErr: false,
		},
		{
			name:     "multi_documents",
			yamlFile: []byte("---\nfield:\n  nested: value\n---\nanother: second\n"),
			want: [][]byte{
				[]byte("field:\n  nested: value"),
				[]byte("another: second"),
			},
			wantErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			docs, err := splitYAML(tt.yamlFile)
			if (err != nil) != tt.wantErr {
				t.Errorf("splitYAML() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if len(tt.want) != len(docs) {
				t.Errorf("splitYAML() produced different number of YAML documents than expected; wanted = %v, got %v", tt.wantNumberOfDocs, len(docs))
			}

			assert.Equal(t, tt.want, docs)
		})
	}
}
