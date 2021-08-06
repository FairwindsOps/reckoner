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
	"io/ioutil"
	"os"
	"strings"

	"gopkg.in/yaml.v3"
	"k8s.io/klog"

	"github.com/fairwindsops/reckoner/pkg/course"
)

// Plot actually plots the releases
func (c Client) Plot() (string, error) {
	err := c.NamespaceManagement()
	if err != nil {
		return "", err
	}

	err = c.UpdateHelmRepos()
	if err != nil {
		return "", err
	}

	err = c.execHook(c.CourseFile.Hooks.PreInstall)
	if err != nil {
		return "", err
	}

	for releaseName, release := range c.CourseFile.Releases {

		err = c.execHook(release.Hooks.PreInstall)
		if err != nil {
			return "", err
		}

		args, tmpFile, err := buildHelmArgs(releaseName, "upgrade", release)
		if err != nil {
			klog.Error(err)
			continue
		}
		if tmpFile != nil {
			defer os.Remove(tmpFile.Name())
		}

		if !c.DryRun {
			out, _, err := c.Helm.Exec(args...)
			if err != nil {
				klog.Error(err)
				continue
			}
			fmt.Println(out)
		} else {
			klog.Warningf("plot not run due to --dry-run: %v", c.DryRun)
			klog.Infof("would have run: helm %s", strings.Join(args, " "))
		}

		err = c.execHook(release.Hooks.PostInstall)
		if err != nil {
			return "", err
		}
	}

	err = c.execHook(c.CourseFile.Hooks.PostInstall)
	if err != nil {
		return "", err
	}

	return "", nil
}

// Template runs the same as plot but runs template instead
func (c Client) Template() (string, error) {
	err := c.UpdateHelmRepos()
	if err != nil {
		return "", nil
	}

	var fullOutput string
	for releaseName, release := range c.CourseFile.Releases {
		args, tmpFile, err := buildHelmArgs(releaseName, "template", release)
		if err != nil {
			klog.Error(err)
			continue
		}
		if tmpFile != nil {
			defer os.Remove(tmpFile.Name())
		}
		out, _, err := c.Helm.Exec(args...)
		if err != nil {
			klog.Error(err)
			continue
		}
		fullOutput = fullOutput + out
	}
	return fullOutput, nil
}

// buildHelmArgs creates a helm command from a release
// takes a command either "upgrade" or "template"
// also returns the temp file of the values file to close
// NOTE: The order is really important here
func buildHelmArgs(releaseName, command string, release course.Release) ([]string, *os.File, error) {
	var valuesFile *os.File
	var args []string
	switch command {
	case "upgrade":
		args = []string{"upgrade", "--install"}
	case "template":
		args = []string{"template"}
	}

	args = append(args, releaseName)
	args = append(args, fmt.Sprintf("%s/%s", release.Repository, release.Chart))

	if release.Values != nil {
		tmpValuesFile, err := makeTempValuesFile(release.Values)
		if err != nil {
			return nil, nil, err
		}
		if tmpValuesFile != nil {
			args = append(args, fmt.Sprintf("--values=%s", tmpValuesFile.Name()))
		} else {
			return nil, nil, fmt.Errorf("unexpected error - got nil temp values file")
		}
		valuesFile = tmpValuesFile
	}

	if len(release.Files) > 0 {
		for _, file := range release.Files {
			args = append(args, fmt.Sprintf("--values=%s", file))
		}
	}

	args = append(args, fmt.Sprintf("--namespace=%s", release.Namespace))

	if release.Version != "" {
		args = append(args, fmt.Sprintf("--version=%s", release.Version))
	}

	return args, valuesFile, nil
}

// makeTempValuesFile puts the values section into a temporary values file
func makeTempValuesFile(values map[string]interface{}) (*os.File, error) {
	tmpFile, err := ioutil.TempFile(os.TempDir(), "reckoner-")
	if err != nil {
		return nil, fmt.Errorf("cannot create temporary file: %s", err)
	}

	valuesData, err := yaml.Marshal(values)
	if err != nil {
		return nil, err
	}
	if _, err = tmpFile.Write(valuesData); err != nil {
		return nil, fmt.Errorf("failed to write to temporary file: %s", err.Error())
	}

	err = tmpFile.Close()
	if err != nil {
		return nil, err
	}

	return tmpFile, nil
}
