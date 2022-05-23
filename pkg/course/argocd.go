package course

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
	Source      ArgoApplicationSpecSource      `yaml:"source"`
	Destination ArgoApplicationSpecDestination `yaml:"destination"`
	Project     string                         `yaml:"project"`
	SyncPolicy  ArgoApplicationSpecSyncPolicy  `yaml:"syncPolicy,omitempty"`
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
