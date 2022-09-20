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

const (
	testReleaseName = "helm-chart"
	testNamespace   = "helm-ns"
)

func TestParseChartVersion(t *testing.T) {
	type test struct {
		name       string
		importInfo *ImportInfo
		want       *ImportInfo
		wantErr    bool
	}
	tests := []test{
		{
			name: "succeed",
			importInfo: &ImportInfo{
				Chart:     "helm-chart-0.1.2",
				Version:   "",
				Name:      testReleaseName,
				Namespace: testNamespace,
			},
			want: &ImportInfo{
				Chart:     "helm-chart",
				Version:   "0.1.2",
				Name:      testReleaseName,
				Namespace: testNamespace,
			},
			wantErr: false,
		},
		{
			name: "error",
			importInfo: &ImportInfo{
				Chart:     "helmchart",
				Version:   "",
				Name:      testReleaseName,
				Namespace: testNamespace,
			},
			want:    &ImportInfo{},
			wantErr: true,
		},
		{
			name: "version error",
			importInfo: &ImportInfo{
				Chart:     "helm-chart",
				Version:   "",
				Name:      testReleaseName,
				Namespace: testNamespace,
			},
			want:    &ImportInfo{},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.importInfo.parseChartVersion()
			got := tt.importInfo
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.EqualValues(t, tt.want, got)
			}
		})
	}
}
