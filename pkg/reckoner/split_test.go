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
