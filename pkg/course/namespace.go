package course

import (
	"k8s.io/klog/v2"
)

// populateNamespaceManagement populates each release with the default namespace management settings if they are not set
func (f *FileV2) populateNamespaceManagement() {
	var emptyNamespaceMgmt NamespaceConfig
	if f.NamespaceMgmt == nil {
		f.NamespaceMgmt = &NamespaceMgmt{}
	}
	if f.NamespaceMgmt.Default == nil {
		f.NamespaceMgmt.Default = &emptyNamespaceMgmt
		f.NamespaceMgmt.Default.Settings.Overwrite = boolPtr(false)
	} else if f.NamespaceMgmt.Default.Settings.Overwrite == nil {
		f.NamespaceMgmt.Default.Settings.Overwrite = boolPtr(false)
	}

	for releaseIndex, release := range f.Releases {
		newRelease := *release
		if newRelease.NamespaceMgmt == nil {
			klog.V(5).Infof("using default namespace management for release: %s", release.Name)
			newRelease.NamespaceMgmt = f.NamespaceMgmt.Default
		} else {
			newRelease.NamespaceMgmt = mergeNamespaceManagement(*f.NamespaceMgmt.Default, *newRelease.NamespaceMgmt)

		}
		f.Releases[releaseIndex] = &newRelease
	}
}

// mergeNamespaceManagement merges the default namespace management settings with the release specific settings
func mergeNamespaceManagement(defaults NamespaceConfig, mergeInto NamespaceConfig) *NamespaceConfig {
	for k, v := range defaults.Metadata.Annotations {
		if mergeInto.Metadata.Annotations == nil {
			mergeInto.Metadata.Annotations = map[string]string{}
		}
		if mergeInto.Metadata.Annotations[k] == "" {
			mergeInto.Metadata.Annotations[k] = v
		}
	}

	for k, v := range defaults.Metadata.Labels {
		if mergeInto.Metadata.Labels == nil {
			mergeInto.Metadata.Labels = map[string]string{}
		}
		if mergeInto.Metadata.Labels[k] == "" {
			mergeInto.Metadata.Labels[k] = v
		}
	}

	if mergeInto.Settings.Overwrite == nil {
		mergeInto.Settings.Overwrite = defaults.Settings.Overwrite
	}

	return &mergeInto
}
