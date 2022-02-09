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
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"strings"

	"github.com/fatih/color"
	"github.com/xeipuuv/gojsonschema"
	"gopkg.in/yaml.v3"
	"k8s.io/klog"
)

// FileV2 is the heart of reckoner, it contains the definitions of the releases to be installed
// as well as all other configuration.
type FileV2 struct {
	// SchemaVersion is the version of the reckoner schema
	SchemaVersion string `yaml:"schema,omitempty" json:"schema,omitempty"`
	// DefaultNamespace is the namespace that releases will be installed into if
	// a namespace is not specified on the Release
	DefaultNamespace string `yaml:"namespace" json:"namespace"`
	// DefaultRepository is the default repository that the release will be installed
	// from if one is not specified on the Release
	DefaultRepository string `yaml:"repository" json:"repository"`
	// Context is the kubeconfig context to use when installing
	// if that context is not available, then reckoner should fail
	Context string `yaml:"context,omitempty" json:"context,omitempty"`
	// Repositories is a list of helm repositories that can be used to look for charts
	Repositories RepositoryList `yaml:"repositories" json:"repositories"`
	// MinimumVersions is a block that restricts this course file from being used with
	// outdated versions of helm or reckoner
	MinimumVersions struct {
		Helm     string `yaml:"helm,omitempty" json:"helm,omitempty"`
		Reckoner string `yaml:"reckoner,omitempty" json:"reckoner,omitempty"`
	} `yaml:"minimum_versions,omitempty" json:"minimum_versions,omitempty"`
	// Hooks is a set of scripts to be run before or after the release is installed.
	Hooks Hooks `yaml:"hooks,omitempty" json:"hooks,omitempty"`
	// NamespaceMgmt contains the default namespace config for all namespaces managed by this course.
	NamespaceMgmt struct {
		// Default is the default namespace config for this course
		Default NamespaceConfig `yaml:"default" json:"default"`
	} `yaml:"namespace_management,omitempty" json:"namespace_management,omitempty"`
	// Releases is the list of releases that should be maintained by this course file.
	Releases []*Release `yaml:"releases" json:"releases"`
}

// Repository is a helm reposotory definition
type Repository struct {
	URL  string `yaml:"url,omitempty" json:"url,omitempty"`
	Git  string `yaml:"git,omitempty" json:"git,omitempty"`
	Path string `yaml:"path,omitempty" json:"path,omitempty"`
}

// RepositoryList is a set of repositories
type RepositoryList map[string]Repository

// Hooks are a set of short scripts to run before or after installation
type Hooks struct {
	// PreInstall hooks run before the release is installed, but after the namespace is created and labelled/annotated
	PreInstall []string `yaml:"pre_install,omitempty" json:"pre_install,omitempty"`
	// PostInstall hooks run after the release is installed. They are skipped if the release installation fails
	PostInstall []string `yaml:"post_install,omitempty" json:"post_install,omitempty"`
}

// NamespaceConfig allows setting namespace annotations and labels
type NamespaceConfig struct {
	Metadata struct {
		Annotations map[string]string `yaml:"annotations,omitempty" json:"annotations,omitempty"`
		Labels      map[string]string `yaml:"labels,omitempty" json:"labels,omitempty"`
	} `yaml:"metadata,omitempty" json:"metadata,omitempty"`
	Settings struct {
		// Overwrite specifies if these annotations and labels should be overwritten in the event that they already exist.
		Overwrite bool `yaml:"overwrite,omitempty" json:"overwrite,omitempty"`
	} `yaml:"settings" json:"settings"`
}

// Release represents a helm release and all of its configuration
type Release struct {
	gitClonePath *string
	// Name is the name of the release
	Name string `yaml:"name" json:"name"`
	// Namespace is the namespace that this release should be placed in
	Namespace string `yaml:"namespace,omitempty" json:"namespace,omitempty"`
	// NamespaceMgmt is a set of labels and annotations to be added to the namespace for this release
	NamespaceMgmt NamespaceConfig `yaml:"namespace_management,omitempty" json:"namespace_management,omitempty"`
	// Chart is the name of the chart used by this release.
	// If empty, then the release name is assumed to be the chart.
	Chart string `yaml:"chart,omitempty" json:"chart,omitempty"`
	// Hooks contains pre and post hooks for a specific release
	Hooks Hooks `yaml:"hooks,omitempty" json:"hooks,omitempty"`
	// Version is the version of the chart to install.
	// If empty, reckoner will use the latest version of the chart in the repository.
	// If this is a git repository, then this should be a git ref.
	// if this is empty, and it is a git repository, then the latest commit on the default
	// branch will be used.
	Version string `yaml:"version,omitempty" json:"version,omitempty"`
	// Repository is the name of the repository that the chart for this release comes from
	// This must correspond to a defined repository in the "header" of the course
	Repository string `yaml:"repository" json:"repository"`
	// Files is a list of external values files that should be passed to helm in addition to values
	Files []string `yaml:"files,omitempty" json:"files,omitempty"`
	// Values contains any values that you wish to pass to the release. Everything
	// underneath this key will placed in a temporary yaml file and passed to helm as a values file.
	Values map[string]interface{} `yaml:"values,omitempty" json:"values,omitempty"`
}

// ReleaseV1 represents a helm release and all of its configuration from v1 schema
type ReleaseV1 struct {
	// Name is the name of the release
	Name string `yaml:"name" json:"name"`
	// Namespace is the namespace that this release should be placed in
	Namespace string `yaml:"namespace,omitempty" json:"namespace,omitempty"`
	// NamespaceMgmt is a set of labels and annotations to be added to the namespace for this release
	NamespaceMgmt NamespaceConfig `yaml:"namespace_management,omitempty" json:"namespace_management,omitempty"`
	// Chart is the name of the chart used by this release
	Chart string `yaml:"chart" json:"chart"`
	// Hooks are pre and post install hooks
	Hooks Hooks `yaml:"hooks,omitempty" json:"hooks,omitempty"`
	// Version is the version of the chart to install
	Version string `yaml:"version" json:"version"`
	// Repository is the repository
	Repository interface{} `yaml:"repository,omitempty" json:"repository,omitempty"`
	// Files is a list of external values files that should be passed to helm in addition to values
	Files []string `yaml:"files,omitempty" json:"files,omitempty"`
	// Values contains any values that you wish to pass to the release. Everything
	// underneath this key will placed in a temporary yaml file and passed to helm as a values file.
	Values map[string]interface{} `yaml:"values" json:"values"`
}

// FileV1 represents the v1 reckoner course structure for purpsoses of conversion
type FileV1 struct {
	// DefaultNamespace is the namespace that releases will be installed into if
	// a namespace is not specified on the Release
	DefaultNamespace string `yaml:"namespace" json:"namespace"`
	// DefaultRepository is the default repository that the release will be installed
	// from if one is not specified on the Release
	DefaultRepository string `yaml:"repository" json:"repository"`
	// Context is the kubeconfig context to use when installing
	// if that context is not available, then reckoner should fail
	Context string `yaml:"context" json:"context"`
	// Repositories is a list of helm repositories that can be used to look for charts
	Repositories RepositoryList `yaml:"repositories" json:"repositories"`
	// MinimumVersions is a block that restricts this course file from being used with
	// outdated versions of helm or reckoner
	MinimumVersions struct {
		Helm     string `yaml:"helm,omitempty" json:"helm,omitempty"`
		Reckoner string `yaml:"reckoner,omitempty" json:"reckoner,omitempty"`
	} `yaml:"minimum_versions,omitempty" json:"minimum_versions,omitempty"`
	// Hooks is a set of scripts to be run before or after the release is installed.
	Hooks Hooks `yaml:"hooks" json:"hooks"`
	// NamespaceMgmt contains the default namespace config for all namespaces managed by this course.
	NamespaceMgmt struct {
		// Default is the default namespace config for this course
		Default NamespaceConfig `yaml:"default" json:"default"`
	} `yaml:"namespace_management" json:"namespace_management"`
	// Charts is the map of releases
	Charts ChartsListV1 `yaml:"charts" json:"charts"`
}

// ChartsListV1 is a list of charts for the v1 schema
type ChartsListV1 []ReleaseV1

// RepositoryV1 is a helm reposotory definition
type RepositoryV1 struct {
	Name string `yaml:"name,omitempty" json:"name,omitempty"`
	URL  string `yaml:"url,omitempty" json:"url,omitempty"`
	Git  string `yaml:"git,omitempty" json:"git,omitempty"`
	Path string `yaml:"path,omitempty" json:"path,omitempty"`
}

// RepositoryV1List is a set of repositories
type RepositoryV1List map[string]Repository

// convertV1toV2 converts the old python course file to the newer golang v2 schema
func convertV1toV2(fileName string) (*FileV2, error) {
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
	newFile.Releases = make([]*Release, len(oldFile.Charts))
	newFile.Hooks = oldFile.Hooks
	newFile.MinimumVersions = oldFile.MinimumVersions

	for releaseIndex, release := range oldFile.Charts {
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

				repositoryName = fmt.Sprintf("%s-git-repository", release.Name)
				newFile.Repositories[repositoryName] = Repository{
					Git:  addRepo.Git,
					Path: addRepo.Path,
				}

			} else {
				// Another legacy style where repository.name was used instead of just repository
				repositoryName = addRepo.Name
			}
		}
		newFile.Releases[releaseIndex] = &Release{
			Name:          release.Name,
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
func OpenCourseV2(fileName string, schema []byte) (*FileV2, error) {
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
		fileV2, errConvert := convertV1toV2(fileName)
		if errConvert != nil {
			return nil, fmt.Errorf("could not unmarshal file from v1 or v2 schema:\n\t%s", errConvert.Error())
		}
		color.Yellow("WARNING: this course file was automatically converted from v1 to v2 at runtime - to convert the file permanently, run \"reckoner convert -i %s\"", fileName)
		courseFile = fileV2
	}

	// Marshal back here just so we can populate the env vars without any yaml comments present
	data, _ = yaml.Marshal(courseFile)
	data, err = parseEnv(data)
	if err != nil {
		return nil, fmt.Errorf("failed to parse env variables: %v", err)
	}
	err = yaml.Unmarshal(data, courseFile)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal file after parsing env vars: %s", err.Error())
	}

	courseFile.populateDefaultNamespace()
	courseFile.populateDefaultRepository()
	courseFile.populateEmptyChartNames()

	if courseFile.SchemaVersion != "v2" {
		return nil, fmt.Errorf("unsupported schema version: %s", courseFile.SchemaVersion)
	}

	if err := courseFile.validateJsonSchema(schema); err != nil {
		return nil, fmt.Errorf("failed to validate jsonSchema in course file: %s", fileName)
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

// UnmarshalYAML implements the yaml.Unmarshaler interface to customize how we Unmarshal this particular field of the FileV1 struct
func (cl *ChartsListV1) UnmarshalYAML(value *yaml.Node) error {
	if value.Kind != yaml.MappingNode {
		return fmt.Errorf("ChartsList must contain YAML mapping, has %v", value.Kind)
	}
	*cl = make([]ReleaseV1, len(value.Content)/2)
	for i := 0; i < len(value.Content); i += 2 {
		var res = &(*cl)[i/2]
		if err := value.Content[i].Decode(&res.Name); err != nil {
			return err
		}
		if err := value.Content[i+1].Decode(&res); err != nil {
			return err
		}
	}
	return nil
}

// populateDefaultNamespace sets the default namespace in each release
// if the release does not have a namespace. If the DefaultNamespace is blank, simply returns
func (f *FileV2) populateDefaultNamespace() {
	if f.DefaultNamespace == "" {
		klog.V(2).Info("no default namespace set - skipping filling out defaults")
		return
	}
	for releaseIndex, release := range f.Releases {
		if release.Namespace == "" {
			klog.V(5).Infof("setting the default namespace of %s on release %s", f.DefaultNamespace, release.Name)
			release.Namespace = f.DefaultNamespace
			f.Releases[releaseIndex] = release
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
	for releaseIndex, release := range f.Releases {
		if release.Repository == "" {
			klog.V(5).Infof("setting the default repository of %s on release %s", f.DefaultRepository, release.Name)
			release.Repository = f.DefaultRepository
			f.Releases[releaseIndex] = release
		}
	}
}

// populateEmptyChartNames assumes that the chart name should be the release name if the chart name is empty
func (f *FileV2) populateEmptyChartNames() {
	for releaseIndex, release := range f.Releases {
		if release.Chart == "" {
			klog.V(5).Infof("assuming chart name is release name for release: %s", release.Name)
			release.Chart = release.Name
			f.Releases[releaseIndex] = release
		}
	}
}

func (f FileV2) validateJsonSchema(schemaData []byte) error {
	klog.V(10).Infof("validating course file against schema: \n%s", string(schemaData))
	schema, err := gojsonschema.NewSchema(gojsonschema.NewBytesLoader(schemaData))
	if err != nil {
		return err
	}

	jsonData, err := json.Marshal(f)
	if err != nil {
		return err
	}

	result, err := schema.Validate(gojsonschema.NewBytesLoader(jsonData))
	if err != nil {
		return err
	}
	if len(result.Errors()) > 0 {
		for _, err := range result.Errors() {
			klog.Errorf("jsonSchema error: %s", err.String())
		}
		return fmt.Errorf("jsonSchema validation failed")
	}
	return nil
}

// SetGitClonePath allows the caller to set the path of a locally stored chart from a git repository already cloned
func (r *Release) SetGitClonePath(path string) error {
	if r.gitClonePath != nil {
		return fmt.Errorf("cannot set GitClonePath on release %s - it is already set to %s", r.Name, *r.gitClonePath)
	}
	r.gitClonePath = &path
	return nil
}

// GitClonePath returns true if a git clone path has been set for this release and also returns said path
func (r Release) GitClonePath() (bool, string) {
	if r.gitClonePath != nil {
		return true, *r.gitClonePath
	}
	return false, ""
}

func parseEnv(data []byte) ([]byte, error) {
	dataWithEnv := os.Expand(string(data), envMapper)
	if strings.Contains(dataWithEnv, "_ENV_NOT_SET_") {
		return nil, fmt.Errorf("course has env variables that are not properly set")
	}
	return []byte(dataWithEnv), nil
}

func envMapper(key string) string {
	v := os.Getenv(key)
	if v == "" {
		color.Red("ERROR: environment variable %s is not set", key)
		return "_ENV_NOT_SET_"
	}
	return v
}
