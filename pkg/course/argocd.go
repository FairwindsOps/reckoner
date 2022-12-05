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

// We may use these imports to track ArgoCD Applications exactly. However,
// this also pulls in kubernetes api packages, which makes reckoner rely
// on particular versions of kubernetes. At the time of writing, no such
// relationship exists. Once we've firmly chosen a path, this comment
// should be removed, and potentially this entire file.
// import (
// 	argoAppv1alpha1 "github.com/argoproj/argo-cd/v2/pkg/apis/application/v1alpha1"
// 	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
// )

type ArgoApplicationSpecSyncPolicyAutomated struct {
	Prune bool `yaml:"prune,omitempty"`
}

type ArgoApplicationSpecSyncPolicy struct {
	Automated ArgoApplicationSpecSyncPolicyAutomated `yaml:"automated,omitempty"`
	Options   []string                               `yaml:"syncOptions,omitempty"`
}

type ArgoApplicationSpecSourceDirectory struct {
	Recurse bool `yaml:"recurse,omitempty"`
}

type ArgoApplicationSpecSource struct {
	Directory ArgoApplicationSpecSourceDirectory `yaml:"directory,omitempty"`
	Path      string                             `yaml:"path"`
	RepoURL   string                             `yaml:"repoURL"`
}

type ArgoApplicationSpecDestination struct {
	Server    string `yaml:"server,omitempty"`
	Namespace string `yaml:"namespace,omitempty"`
}

type ArgoApplicationSpec struct {
	Source            ArgoApplicationSpecSource       `yaml:"source"`
	Destination       ArgoApplicationSpecDestination  `yaml:"destination"`
	Project           string                          `yaml:"project"`
	SyncPolicy        ArgoApplicationSpecSyncPolicy   `yaml:"syncPolicy,omitempty"`
	IgnoreDifferences []ArgoResourceIgnoreDifferences `yaml:"ignoreDifferences,omitempty"`
}

// ArgoApplicationMetadata contains the k8s metadata for the gitops agent CustomResource.
// This is the resource/manifest/config the agent will read in, not the resources deployed by the agent.
type ArgoApplicationMetadata struct {
	Name        string            `yaml:"name"`
	Namespace   string            `yaml:"namespace,omitempty"`
	Annotations map[string]string `yaml:"annotations,omitempty"`
	Labels      map[string]string `yaml:"labels,omitempty"`
}

type ArgoApplication struct {
	Kind       string                  `yaml:"kind"`
	APIVersion string                  `yaml:"apiVersion"`
	Metadata   ArgoApplicationMetadata `yaml:"metadata"`
	Spec       ArgoApplicationSpec     `yaml:"spec"`
}

// ResourceIgnoreDifferences contains resource filter and list of json paths which should be ignored during comparison with live state.
type ArgoResourceIgnoreDifferences struct {
	Group             string   `yaml:"group,omitempty"`
	Kind              string   `yaml:"kind"`
	Name              string   `yaml:"name,omitempty"`
	Namespace         string   `yaml:"namespace,omitempty"`
	JSONPointers      []string `yaml:"jsonPointers,omitempty"`
	JQPathExpressions []string `yaml:"jqPathExpressions,omitempty"`
	// ManagedFieldsManagers is a list of trusted managers. Fields mutated by those managers will take precedence over the
	// desired state defined in the SCM and won't be displayed in diffs
	ManagedFieldsManagers []string `yaml:"managedFieldsManagers,omitempty"`
}
