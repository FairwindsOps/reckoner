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

package reckoner

import (
	"fmt"
	"os"
	"path"
	"regexp"
	"sync"

	"k8s.io/client-go/kubernetes"
	"k8s.io/klog/v2"

	// This is required to auth to cloud providers (i.e. GKE)
	_ "k8s.io/client-go/plugin/pkg/client/auth"
	"sigs.k8s.io/controller-runtime/pkg/client/config"

	"github.com/Masterminds/semver/v3"
	"github.com/fairwindsops/reckoner/pkg/course"
	"github.com/fairwindsops/reckoner/pkg/helm"
	"github.com/thoas/go-funk"
)

// Client is a configuration struct
type Client struct {
	KubeClient       kubernetes.Interface
	Helm             helm.Client
	ReckonerVersion  string
	CourseFile       course.FileV2
	PlotAll          bool
	Releases         []string
	BaseDirectory    string
	DryRun           bool
	CreateNamespaces bool
	ContinueOnError  bool
	Errors           int
}

var once sync.Once
var clientset *kubernetes.Clientset

// NewClient returns a client. Attempts to open a v2 schema course file
// If getClient is true, attempts to get a Kubernetes client from config
func NewClient(fileName, version string, plotAll bool, releases []string, kubeClient bool, dryRun bool, createNamespaces bool, schema []byte, continueOnError bool) (*Client, error) {
	// Get the course file
	courseFile, err := course.OpenCourseV2(fileName, schema)
	if err != nil {
		return nil, err
	}

	// Get a helm client
	helmClient, err := helm.NewClient()
	if err != nil {
		return nil, err
	}

	client := &Client{
		CourseFile:       *courseFile,
		PlotAll:          plotAll,
		Releases:         releases,
		Helm:             *helmClient,
		ReckonerVersion:  version,
		BaseDirectory:    path.Dir(fileName),
		DryRun:           dryRun,
		CreateNamespaces: createNamespaces,
		ContinueOnError:  continueOnError,
	}

	// Check versions
	if !client.helmVersionValid() {
		return nil, fmt.Errorf("helm version check failed")
	}
	if !client.reckonerVersionValid() {
		return nil, fmt.Errorf("reckoner version check failed")
	}

	if err := client.filterReleases(); err != nil {
		return nil, err
	}

	if kubeClient {
		client.KubeClient = getKubeClient()
	}

	return client, nil
}

func (c *Client) Continue() bool {
	if c.ContinueOnError {
		c.Errors += 1
		return true
	}
	return false
}

func getKubeClient() *kubernetes.Clientset {
	once.Do(func() {
		kubeConf, err := config.GetConfig()
		if err != nil {
			fmt.Println("Error getting kubeconfig:", err)
			os.Exit(1)
		}
		clientset, err = kubernetes.NewForConfig(kubeConf)
		if err != nil {
			fmt.Println("Error creating kubernetes client:", err)
			os.Exit(1)
		}
	})

	return clientset
}

// helmVersionValid determines if the current helm version high enough
func (c Client) helmVersionValid() bool {
	if c.CourseFile.MinimumVersions.Helm == "" {
		klog.V(2).Infof("no minimum helm version found, assuming okay")
		return true
	}
	currentVersion, err := c.Helm.Version()
	if err != nil {
		klog.Errorf("error getting current helm version: %s", err.Error())
		return false
	}
	klog.V(3).Infof("current helm version: %s", currentVersion.String())

	constraintString := fmt.Sprintf(">=%s", c.CourseFile.MinimumVersions.Helm)
	constraint, err := semver.NewConstraint(constraintString)
	if err != nil {
		klog.Errorf("could not parse helm minimum version: %s", err.Error())
		return false
	}
	klog.V(3).Infof("using helm version constraint: %s", constraintString)
	return constraint.Check(currentVersion)
}

// reckonerVersionValid determines if the current helm version high enough
func (c Client) reckonerVersionValid() bool {
	if c.CourseFile.MinimumVersions.Reckoner == "" {
		klog.V(2).Infof("no minimum reckoner version found, assuming okay")
		return true
	}
	if c.ReckonerVersion == "0.0.0" {
		klog.V(2).Infof("development version of reckoner found - skipping version check")
		return true
	}
	currentVersion, err := semver.NewVersion(c.ReckonerVersion)
	if err != nil {
		klog.Errorf("error parsing current reckoner version: %s", err.Error())
		return false
	}
	klog.V(3).Infof("current reckoner version: %s", currentVersion.String())

	constraintString := fmt.Sprintf(">=%s", c.CourseFile.MinimumVersions.Reckoner)
	constraint, err := semver.NewConstraint(constraintString)
	if err != nil {
		klog.Errorf("could not parse reckoner minimum version: %s", err.Error())
		return false
	}
	klog.V(3).Infof("using reckoner version constraint: %s", constraintString)
	return constraint.Check(currentVersion)
}

// UpdateHelmRepos updates Helm repos
// TODO actually return an error if any are encountered
func (c Client) UpdateHelmRepos() error {
	for repoName, repo := range c.CourseFile.Repositories {
		if repo.URL != "" {
			err := c.Helm.AddRepository(repoName, repo.URL)
			if err != nil {
				klog.Error(err)
			}
		}
	}
	return nil
}

// filterReleases filters the releases based on the client release list
// Use this before you interact with the releases
func (c *Client) filterReleases() error {
	releases := c.CourseFile.Releases
	if len(c.Releases) > 0 {
		selectedReleases := []*course.Release{}
		for _, releaseName := range c.Releases {
			contained := funk.Contains(c.CourseFile.Releases, func(rel *course.Release) bool {
				return rel.Name == releaseName
			})
			if !contained {
				continue
			}
			releaseIndex := funk.IndexOf(c.CourseFile.Releases, func(rel *course.Release) bool {
				return rel.Name == releaseName
			})
			selectedReleases = append(selectedReleases, c.CourseFile.Releases[releaseIndex])
		}
		releases = selectedReleases
	}
	if len(releases) < 1 {
		if c.PlotAll {
			return fmt.Errorf("no valid releases found in course file")
		}
		return fmt.Errorf("no valid releases found in course that match input releases")
	}
	releases, err := c.prepareGitRepositories(releases)
	if err != nil {
		return err
	}
	c.CourseFile.Releases = releases
	return nil
}

// prepareGitRepositories checks each release provided for a git repository and prepares the struct with the proper information needed to clone
func (c *Client) prepareGitRepositories(releases []*course.Release) ([]*course.Release, error) {
	for _, release := range releases {
		repository := c.CourseFile.Repositories[release.Repository]
		if repository.Git != "" {
			cacheDir, err := c.Helm.Cache()
			if err != nil {
				return releases, err
			}
			re := regexp.MustCompile(`\:\/\/|\/|\.`)
			repoPathName := re.ReplaceAllString(repository.Git, "_")
			clonePath := fmt.Sprintf("%s/%s_goreckoner", cacheDir, repoPathName)

			err = release.SetGitPaths(clonePath, fmt.Sprintf("%s/%s", repository.Path, release.Chart))
			if err != nil {
				return releases, err
			}
		}
	}
	return releases, nil
}
