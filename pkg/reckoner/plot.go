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
	"github.com/fatih/color"
	"github.com/thoas/go-funk"
)

// Plot actually plots the releases
func (c Client) Plot() error {
	err := c.NamespaceManagement()
	if err != nil {
		return err
	}

	err = c.UpdateHelmRepos()
	if err != nil {
		return err
	}

	err = c.execHook(c.CourseFile.Hooks.PreInstall)
	if err != nil {
		return err
	}

	for _, release := range c.CourseFile.Releases {

		err = c.execHook(release.Hooks.PreInstall)
		if err != nil {
			return err
		}

		args, tmpFile, err := buildHelmArgs(release.Name, "upgrade", *release)
		if err != nil {
			klog.Error(err)
			continue
		}
		if tmpFile != nil {
			defer os.Remove(tmpFile.Name())
		}

		if !c.DryRun {
			out, stdErr, err := c.Helm.Exec(args...)
			if err != nil {
				return fmt.Errorf("error plotting release %s: %s", release.Name, stdErr)
			}
			fmt.Println(out)
		} else {
			color.Yellow("plot not run due to --dry-run: %v", c.DryRun)
			color.Yellow("would have run: helm %s", strings.Join(args, " "))
		}

		err = c.execHook(release.Hooks.PostInstall)
		if err != nil {
			return err
		}
	}

	err = c.execHook(c.CourseFile.Hooks.PostInstall)
	if err != nil {
		return err
	}

	return nil
}

// TemplateAll runs the same as plot but runs template instead
func (c Client) TemplateAll() (string, error) {
	err := c.UpdateHelmRepos()
	if err != nil {
		return "", nil
	}

	var fullOutput string
	for _, release := range c.CourseFile.Releases {
		out, err := c.TemplateRelease(release.Name)
		if err != nil {
			klog.Error(err)
			continue
		}
		fullOutput = fullOutput + out
	}
	return fullOutput, nil
}

// TemplateRelease does the same thing as TemplateAll but only for one release
func (c Client) TemplateRelease(releaseName string) (string, error) {
	releaseIndex := funk.IndexOf(c.CourseFile.Releases, func(release *course.Release) bool {
		return release.Name == releaseName
	})
	args, tmpFile, err := buildHelmArgs(releaseName, "template", *c.CourseFile.Releases[releaseIndex])
	if err != nil {
		return "", err
	}
	if tmpFile != nil {
		defer os.Remove(tmpFile.Name())
	}
	out, stdErr, _ := c.Helm.Exec(args...)
	if err != nil {
		return "", fmt.Errorf("error templating release %s: %s", releaseName, stdErr)
	}
	return out, nil
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
