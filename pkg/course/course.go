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
	"fmt"
	"io/ioutil"

	"gopkg.in/yaml.v3"
	"k8s.io/klog"
)

// FileV2 is the heart of reckoner, it contains the definitions of the releases to be installed
// as well as all other configuration.
type FileV2 struct {
	// SchemaVersion is the version of the reckoner schema
	SchemaVersion string `yaml:"schema,omitempty"`
	// DefaultNamespace is the namespace that releases will be installed into if
	// a namespace is not specified on the Release
	DefaultNamespace string `yaml:"namespace"`
	// DefaultRepository is the default repository that the release will be installed
	// from if one is not specified on the Release
	DefaultRepository string `yaml:"repository"`
	// Context is the kubeconfig context to use when installing
	// if that context is not available, then reckoner should fail
	Context string `yaml:"context,omitempty"`
	// Repositories is a list of helm repositories that can be used to look for charts
	Repositories RepositoryList `yaml:"repositories"`
	// MinimumVersions is a block that restricts this course file from being used with
	// outdated versions of helm or reckoner
	MinimumVersions struct {
		Helm     string `yaml:"helm,omitempty"`
		Reckoner string `yaml:"reckoner,omitempty"`
	} `yaml:"minimum_versions,omitempty"`
	// Hooks is a set of scripts to be run before or after the release is installed.
	Hooks Hooks `yaml:"hooks,omitempty"`
	// NamespaceMgmt contains the default namespace config for all namespaces managed by this course.
	NamespaceMgmt struct {
		// Default is the default namespace config for this course
		Default NamespaceConfig `yaml:"default"`
	} `yaml:"namespace_management,omitempty"`
	// Releases is the list of releases that should be maintained by this course file.
	Releases ReleaseList `yaml:"releases"`
}

// Repository is a helm reposotory definition
type Repository struct {
	URL  string `yaml:"url,omitempty"`
	Git  string `yaml:"git,omitempty"`
	Path string `yaml:"path,omitempty"`
}

// RepositoryList is a set of repositories
type RepositoryList map[string]Repository

// Hooks are a set of short scripts to run before or after installation
type Hooks struct {
	// PreInstall hooks run before the release is installed, but after the namespace is created and labelled/annotated
	PreInstall []string `yaml:"pre_install,omitempty"`
	// PostInstall hooks run after the release is installed. They are skipped if the release installation fails
	PostInstall []string `yaml:"post_install,omitempty"`
}

// NamespaceConfig allows setting namespace annotations and labels
type NamespaceConfig struct {
	Metadata struct {
		Annotations map[string]string `yaml:"annotations,omitempty"`
		Labels      map[string]string `yaml:"labels,omitempty"`
	} `yaml:"metadata,omitempty"`
	Settings struct {
		// Overwrite specifies if these annotations and labels should be overwritten in the event that they already exist.
		Overwrite bool `yaml:"overwrite,omitempty"`
	} `yaml:"settings"`
}

// Release represents a helm release and all of its configuration
type Release struct {
	// Namespace is the namespace that this release should be placed in
	Namespace string `yaml:"namespace,omitempty"`
	// NamespaceMgmt is a set of labels and annotations to be added to the namespace for this release
	NamespaceMgmt NamespaceConfig `yaml:"namespace_management,omitempty"`
	// Chart is the name of the chart used by this release.
	// If empty, then the release name is assumed to be the chart.
	Chart string `yaml:"chart,omitempty"`
	// Hooks contains pre and post hooks for a specific release
	Hooks Hooks `yaml:"hooks,omitempty"`
	// Version is the version of the chart to install.
	// If empty, reckoner will use the latest version of the chart in the repository.
	// If this is a git repository, then this should be a git ref.
	// if this is empty, and it is a git repository, then the latest commit on the default
	// branch will be used.
	Version string `yaml:"version,omitempty"`
	// Repository is the name of the repository that the chart for this release comes from
	// This must correspond to a defined repository in the "header" of the course
	Repository string `yaml:"repository"`
	// Files is a list of external values files that should be passed to helm in addition to values
	Files []string `yaml:"files,omitempty"`
	// Values contains any values that you wish to pass to the release. Everything
	// underneath this key will placed in a temporary yaml file and passed to helm as a values file.
	Values map[string]interface{} `yaml:"values,omitempty"`
}

// ReleaseList is a set of releases
type ReleaseList map[string]Release

// ReleaseV1 represents a helm release and all of its configuration from v1 schema
type ReleaseV1 struct {
	// Namespace is the namespace that this release should be placed in
	Namespace string `yaml:"namespace,omitempty"`
	// NamespaceMgmt is a set of labels and annotations to be added to the namespace for this release
	NamespaceMgmt NamespaceConfig `yaml:"namespace_management,omitempty"`
	// Chart is the name of the chart used by this release
	Chart string `yaml:"chart"`
	// Hooks are pre and post install hooks
	Hooks Hooks `yaml:"hooks,omitempty"`
	// Version is the version of the chart to install
	Version string `yaml:"version"`
	// Repository is the repository
	Repository interface{} `yaml:"repository,omitempty"`
	// Files is a list of external values files that should be passed to helm in addition to values
	Files []string `yaml:"files,omitempty"`
	// Values contains any values that you wish to pass to the release. Everything
	// underneath this key will placed in a temporary yaml file and passed to helm as a values file.
	Values map[string]interface{} `yaml:"values"`
}

// FileV1 represents the v1 reckoner course structure for purpsoses of conversion
type FileV1 struct {
	// DefaultNamespace is the namespace that releases will be installed into if
	// a namespace is not specified on the Release
	DefaultNamespace string `yaml:"namespace"`
	// DefaultRepository is the default repository that the release will be installed
	// from if one is not specified on the Release
	DefaultRepository string `yaml:"repository"`
	// Context is the kubeconfig context to use when installing
	// if that context is not available, then reckoner should fail
	Context string `yaml:"context"`
	// Repositories is a list of helm repositories that can be used to look for charts
	Repositories RepositoryList `yaml:"repositories"`
	// MinimumVersions is a block that restricts this course file from being used with
	// outdated versions of helm or reckoner
	MinimumVersions struct {
		Helm     string `yaml:"helm"`
		Reckoner string `yaml:"reckoner"`
	} `yaml:"minimum_versions"`
	// Hooks is a set of scripts to be run before or after the release is installed.
	Hooks Hooks `yaml:"hooks"`
	// NamespaceMgmt contains the default namespace config for all namespaces managed by this course.
	NamespaceMgmt struct {
		// Default is the default namespace config for this course
		Default NamespaceConfig `yaml:"default"`
	} `yaml:"namespace_management"`
	// Charts is the map of releases
	Charts map[string]ReleaseV1
}

// RepositoryV1 is a helm reposotory definition
type RepositoryV1 struct {
	Name string `yaml:"name,omitempty"`
	URL  string `yaml:"url,omitempty"`
	Git  string `yaml:"git,omitempty"`
	Path string `yaml:"path,omitempty"`
}

// RepositoryV1List is a set of repositories
type RepositoryV1List map[string]Repository

// ConvertV1toV2 converts the old python course file to the newer golang v2 schema
func ConvertV1toV2(fileName string) (*FileV2, error) {
	newFile := &FileV2{
		SchemaVersion: "v2",
	}

	oldFile, err := OpenCourseV1(fileName)
	if err != nil {
		return nil, err
	}

	// These things are all equivalent
	newFile.DefaultNamespace = oldFile.DefaultNamespace
	newFile.Context = oldFile.Context
	newFile.NamespaceMgmt = oldFile.NamespaceMgmt
	newFile.DefaultRepository = oldFile.DefaultRepository
	newFile.Repositories = oldFile.Repositories
	newFile.Releases = make(map[string]Release)
	newFile.Hooks = oldFile.Hooks

	for releaseName, release := range oldFile.Charts {
		repositoryName, ok := release.Repository.(string)
		// The repository is not in the format repository: string. Need to handle that
		if !ok {
			addRepo := &RepositoryV1{}
			data, err := yaml.Marshal(release.Repository)
			if err != nil {
				return nil, err
			}
			err = yaml.Unmarshal(data, addRepo)
			if err != nil {
				return nil, err
			}
			// Find old style git repositories
			if addRepo.Git != "" {
				klog.V(3).Infof("detected a git-based inline repository. Attempting to convert to repository in header")

				repositoryName = fmt.Sprintf("%s-git-repository", releaseName)
				newFile.Repositories[repositoryName] = Repository{
					Git:  addRepo.Git,
					Path: addRepo.Path,
				}

			} else {
				// Another legacy style where repository.name was used instead of just repository
				repositoryName = addRepo.Name
			}
		}
		newFile.Releases[releaseName] = Release{
			Namespace:     release.Namespace,
			NamespaceMgmt: release.NamespaceMgmt,
			Repository:    repositoryName,
			Chart:         release.Chart,
			Version:       release.Version,
			Values:        release.Values,
			Hooks:         release.Hooks,
		}
	}
	return newFile, nil
}

// OpenCourseV2 opens a v2 schema course file
func OpenCourseV2(fileName string) (*FileV2, error) {
	courseFile := &FileV2{}
	data, err := ioutil.ReadFile(fileName)
	if err != nil {
		return nil, err
	}
	err = yaml.Unmarshal(data, courseFile)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal file: %s", err.Error())
	}
	if courseFile.SchemaVersion != "v2" {
		klog.V(2).Infof("did not detect v2 course file - trying conversion from v1")
		fileV2, errConvert := ConvertV1toV2(fileName)
		if errConvert != nil {
			return nil, fmt.Errorf("could not unmarshal file from v1 or v2 schema")
		}
		klog.Info("WARNING: this course file was automatically converted from v1 to v2 - this functionality may be removed in the future")
		courseFile = fileV2
	}

	courseFile.populateDefaultNamespace()
	courseFile.populateDefaultRepository()
	courseFile.populateEmptyChartNames()

	if courseFile.SchemaVersion != "v2" {
		return nil, fmt.Errorf("unsupported schema version: %s", courseFile.SchemaVersion)
	}
	return courseFile, nil
}

// OpenCourseV1 opens a v1 schema course file
func OpenCourseV1(fileName string) (*FileV1, error) {
	courseFile := &FileV1{}
	data, err := ioutil.ReadFile(fileName)
	if err != nil {
		return nil, err
	}
	err = yaml.Unmarshal(data, courseFile)
	if err != nil {
		return nil, err
	}

	return courseFile, nil
}

// populateDefaultNamespace sets the default namespace in each release
// if the release does not have a namespace. If the DefaultNamespace is blank, simply returns
func (f *FileV2) populateDefaultNamespace() {
	if f.DefaultNamespace == "" {
		klog.V(2).Info("no default namespace set - skipping filling out defaults")
		return
	}
	for releaseName, release := range f.Releases {
		if release.Namespace == "" {
			klog.V(5).Infof("setting the default namespace of %s on release %s", f.DefaultNamespace, releaseName)
			release.Namespace = f.DefaultNamespace
			f.Releases[releaseName] = release
		}
	}
}

// populateDefaultRepository sets the default repository in each release
// if the release does not have a repository specified. If the DefaultRepository is blank, simply returns.
func (f *FileV2) populateDefaultRepository() {
	if f.DefaultRepository == "" {
		klog.V(2).Info("no default repository set - skipping filling out defaults")
		return
	}
	for releaseName, release := range f.Releases {
		if release.Repository == "" {
			klog.V(5).Infof("setting the default repository of %s on release %s", f.DefaultRepository, releaseName)
			release.Repository = f.DefaultRepository
			f.Releases[releaseName] = release
		}
	}
}

// populateEmptyChartNames assumes that the chart name should be the release name if the chart name is empty
func (f *FileV2) populateEmptyChartNames() {
	for releaseName, release := range f.Releases {
		if release.Chart == "" {
			klog.V(5).Infof("assuming chart name is release name for release: %s", releaseName)
			release.Chart = releaseName
			f.Releases[releaseName] = release
		}
	}
}
