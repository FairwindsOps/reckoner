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
	"sync"

	"k8s.io/client-go/kubernetes"
	"k8s.io/klog"

	// This is required to auth to cloud providers (i.e. GKE)
	_ "k8s.io/client-go/plugin/pkg/client/auth"
	"sigs.k8s.io/controller-runtime/pkg/client/config"

	"github.com/Masterminds/semver"
	"github.com/fairwindsops/reckoner/pkg/course"
	"github.com/fairwindsops/reckoner/pkg/helm"
)

// Client is a configuration struct
type Client struct {
	KubeClient      kubernetes.Interface
	Helm            helm.Client
	ReckonerVersion string
	CourseFile      course.FileV2
	PlotAll         bool
	Releases        []string
}

var once sync.Once
var clientset *kubernetes.Clientset

// NewClient returns a client. Attempts to open a v2 schema course file
// If getClient is true, attempts to get a Kubernetes client from config
func NewClient(fileName, version string, plotAll bool, releases []string, kubeClient bool) (*Client, error) {
	// Get the course file
	courseFile, err := course.OpenCourseV2(fileName)
	if err != nil {
		return nil, err
	}

	// Get a helm client
	helmClient, err := helm.NewClient()
	if err != nil {
		return nil, err
	}

	client := &Client{
		CourseFile:      *courseFile,
		PlotAll:         plotAll,
		Releases:        releases,
		Helm:            *helmClient,
		ReckonerVersion: version,
	}

	// Check versions
	if !client.HelmVersionValid() {
		return nil, fmt.Errorf("helm version check failed")
	}
	if !client.ReckonerVersionValid() {
		return nil, fmt.Errorf("reckoner version check failed")
	}

	if kubeClient {
		client.KubeClient = getKubeClient()
	}

	return client, nil
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

// HelmVersionValid determines if the current helm version high enough
func (c Client) HelmVersionValid() bool {
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

// ReckonerVersionValid determines if the current helm version high enough
func (c Client) ReckonerVersionValid() bool {
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
