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

package course

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func Test_mergeNamespaceManagement(t *testing.T) {
	type args struct {
		defaults  NamespaceConfig
		mergeInto NamespaceConfig
	}
	tests := []struct {
		name string
		args args
		want *NamespaceConfig
	}{
		{
			name: "basic merge",
			args: args{
				defaults: NamespaceConfig{
					Metadata: NSMetadata{
						Annotations: map[string]string{
							"default-annotation": "default-value",
						},
						Labels: map[string]string{
							"default-label": "default-value",
						},
					},
					Settings: NSSettings{
						Overwrite: boolPtr(false),
					},
				},
				mergeInto: NamespaceConfig{
					Metadata: NSMetadata{
						Annotations: map[string]string{
							"merge-annotation": "merge-value",
						},
						Labels: map[string]string{
							"merge-label": "merge-value",
						},
					},
					Settings: NSSettings{
						Overwrite: boolPtr(false),
					},
				},
			},
			want: &NamespaceConfig{
				Metadata: NSMetadata{
					Annotations: map[string]string{
						"default-annotation": "default-value",
						"merge-annotation":   "merge-value",
					},
					Labels: map[string]string{
						"default-label": "default-value",
						"merge-label":   "merge-value",
					},
				},
				Settings: NSSettings{
					Overwrite: boolPtr(false),
				},
			},
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := mergeNamespaceManagement(tt.args.defaults, tt.args.mergeInto)
			assert.EqualValues(t, tt.want, got)
		})
	}
}

func TestFileV2_populateNamespaceManagement(t *testing.T) {
	tests := []struct {
		name string
		file *FileV2
		want *FileV2
	}{
		{
			name: "empty default",
			file: &FileV2{
				Releases:      []*Release{},
				NamespaceMgmt: &NamespaceMgmt{},
			},
			want: &FileV2{
				NamespaceMgmt: &NamespaceMgmt{
					Default: &NamespaceConfig{
						Settings: NSSettings{
							Overwrite: boolPtr(false),
						},
					},
				},
				Releases: []*Release{},
			},
		},
		{
			name: "empty default overwrite",
			file: &FileV2{
				Releases: []*Release{},
				NamespaceMgmt: &NamespaceMgmt{
					Default: &NamespaceConfig{
						Settings: NSSettings{
							Overwrite: nil,
						},
					},
				},
			},
			want: &FileV2{
				NamespaceMgmt: &NamespaceMgmt{
					Default: &NamespaceConfig{
						Settings: NSSettings{
							Overwrite: boolPtr(false),
						},
					},
				},
				Releases: []*Release{},
			},
		},
		{
			name: "release default",
			file: &FileV2{
				Releases: []*Release{
					{
						Name: "default",
					},
				},
				NamespaceMgmt: &NamespaceMgmt{
					Default: nil,
				},
			},
			want: &FileV2{
				NamespaceMgmt: &NamespaceMgmt{
					Default: &NamespaceConfig{
						Settings: NSSettings{
							Overwrite: boolPtr(false),
						},
					},
				},
				Releases: []*Release{
					{
						Name: "default",
						NamespaceMgmt: &NamespaceConfig{
							Settings: NSSettings{
								Overwrite: boolPtr(false),
							},
						},
					},
				},
			},
		},
		{
			name: "release specific",
			file: &FileV2{
				Releases: []*Release{
					{
						Name: "default",
						NamespaceMgmt: &NamespaceConfig{
							Settings: NSSettings{
								Overwrite: boolPtr(false),
							},
							Metadata: NSMetadata{
								Annotations: map[string]string{
									"release-annotation": "release-value",
								},
								Labels: map[string]string{
									"release-label": "release-value",
								},
							},
						},
					},
					{
						Name:          "release2",
						NamespaceMgmt: &NamespaceConfig{},
					},
				},
				NamespaceMgmt: &NamespaceMgmt{
					Default: &NamespaceConfig{
						Settings: NSSettings{},
						Metadata: NSMetadata{
							Annotations: map[string]string{
								"course-annotation": "course-value",
							},
							Labels: map[string]string{
								"course-label": "course-value",
							},
						},
					},
				},
			},
			want: &FileV2{
				NamespaceMgmt: &NamespaceMgmt{
					Default: &NamespaceConfig{
						Settings: NSSettings{
							Overwrite: boolPtr(false),
						},
						Metadata: NSMetadata{
							Annotations: map[string]string{
								"course-annotation": "course-value",
							},
							Labels: map[string]string{
								"course-label": "course-value",
							},
						},
					},
				},
				Releases: []*Release{
					{
						Name: "default",
						NamespaceMgmt: &NamespaceConfig{
							Settings: NSSettings{
								Overwrite: boolPtr(false),
							},
							Metadata: NSMetadata{
								Annotations: map[string]string{
									"course-annotation":  "course-value",
									"release-annotation": "release-value",
								},
								Labels: map[string]string{
									"course-label":  "course-value",
									"release-label": "release-value",
								},
							},
						},
					},
					{
						Name: "release2",
						NamespaceMgmt: &NamespaceConfig{
							Settings: NSSettings{
								Overwrite: boolPtr(false),
							},
							Metadata: NSMetadata{
								Annotations: map[string]string{
									"course-annotation": "course-value",
								},
								Labels: map[string]string{
									"course-label": "course-value",
								},
							},
						},
					},
				},
			},
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tt.file.populateNamespaceManagement()
			assert.EqualValues(t, tt.want, tt.file)
		})
	}
}
