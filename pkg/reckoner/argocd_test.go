package reckoner

import (
	"testing"

	"github.com/fairwindsops/reckoner/pkg/course"
	"github.com/stretchr/testify/assert"
)

func Test_generateArgoApplication(t *testing.T) {
	tests := []struct {
		name    string
		cFile   course.FileV2
		want    course.ArgoApplication
		wantErr bool
	}{
		{
			name: "ensure_defaults",
			cFile: course.FileV2{
				Releases: []*course.Release{
					{
						Name:       "somename",
						Namespace:  "somens",
						Repository: "somerepo",
						GitOps: course.GitOps{ // release-specific *addition*
							ArgoCD: course.ArgoApplication{
								Metadata: course.ArgoApplicationMetadata{
									Annotations: map[string]string{
										"notifications.argoproj.io/subscribe.on-sync-succeeded.slack": "fairwindsops-infra-argocd",
									},
								},
								Spec: course.ArgoApplicationSpec{
									Source: course.ArgoApplicationSpecSource{
										Directory: course.ArgoApplicationSpecSourceDirectory{
											Recurse: true, // release-specific *override*
										},
									},
								},
							},
						},
					},
				},
				GitOps: course.GitOps{
					ArgoCD: course.ArgoApplication{
						Spec: course.ArgoApplicationSpec{
							Source: course.ArgoApplicationSpecSource{
								Directory: course.ArgoApplicationSpecSourceDirectory{
									Recurse: false, // exists here only to be overridden by the release-specific instance
								},
								// Path:    "somepath", // omitting this tests more functionality
								RepoURL: "https://domain.tld/someorg/somerepo.git",
							},
							// Destination: course.ArgoApplicationSpecDestination{}, // omitting this tests defaults
						},
					},
				},
			},
			want: course.ArgoApplication{
				Kind:       "Application",
				APIVersion: "argoproj.io/v1alpha1",
				Metadata: course.ArgoApplicationMetadata{
					Name: "somename",
					Annotations: map[string]string{
						"notifications.argoproj.io/subscribe.on-sync-succeeded.slack": "fairwindsops-infra-argocd",
					},
				},
				Spec: course.ArgoApplicationSpec{
					Source: course.ArgoApplicationSpecSource{
						Directory: course.ArgoApplicationSpecSourceDirectory{
							Recurse: true,
						},
						Path:    "somename",
						RepoURL: "https://domain.tld/someorg/somerepo.git",
					},
					Destination: course.ArgoApplicationSpecDestination{
						Server:    "https://kubernetes.default.svc",
						Namespace: "somens",
					},
					Project: "default",
				},
			},
			wantErr: false,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := generateArgoApplication(*tt.cFile.Releases[0], tt.cFile)
			if (err != nil) != tt.wantErr {
				t.Errorf("generateArgoApplication() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			assert.Equal(t, tt.want, got)
		})
	}
}
