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
	"strings"

	"gopkg.in/yaml.v3"

	"github.com/fairwindsops/reckoner/pkg/course"
	"github.com/fatih/color"
	"github.com/thoas/go-funk"
)

// Plot actually plots the releases
func (c *Client) Plot() error {
	err := c.NamespaceManagement()
	if err != nil {
		return err
	}

	err = c.UpdateHelmRepos()
	if err != nil {
		return err
	}

	err = c.execHook(c.CourseFile.Hooks.PreInstall, "course pre")
	if err != nil {
		if !c.Continue() {
			return err
		}
	}

	for _, release := range c.CourseFile.Releases {

		err = c.execHook(release.Hooks.PreInstall, "release pre")
		if err != nil {
			if c.Continue() {
				color.Red("error with release %s: %s, continuing.", release.Name, err.Error())
				continue
			}
			return err
		}

		args, tmpFile, err := buildHelmArgs("upgrade", c.BaseDirectory, *release, c.CourseFile.HelmArgs)
		if err != nil {
			color.Red(err.Error())
			continue
		}
		if tmpFile != nil {
			defer os.Remove(tmpFile.Name())
		}

		if err := c.cloneGitRepo(release); err != nil {
			if c.Continue() {
				color.Red(err.Error())
				continue
			}
			return err
		}

		if !c.DryRun {
			out, stdErr, err := c.Helm.Exec(args...)
			if err != nil {
				if c.Continue() {
					color.Red("error with release %s: %s, continuing.", release.Name, err.Error())
					continue
				}
				return fmt.Errorf("error plotting release %s: %s", release.Name, stdErr)
			}
			fmt.Println(out)
		} else {
			color.Yellow("plot not run due to --dry-run: %v", c.DryRun)
			color.Yellow("would have run: helm %s", strings.Join(args, " "))
		}

		err = c.execHook(release.Hooks.PostInstall, "release post")
		if err != nil {
			if c.Continue() {
				color.Red("error with release %s: %s, continuing.", release.Name, err.Error())
				continue
			}
			return err
		}
	}

	err = c.execHook(c.CourseFile.Hooks.PostInstall, "course post")
	if err != nil {
		if !c.Continue() {
			return err
		}
	}

	return nil
}

// TemplateAll runs the same as plot but runs template instead
func (c Client) TemplateAll() (fullOutput string, err error) {
	err = c.UpdateHelmRepos()
	if err != nil {
		return fullOutput, err
	}

	for _, release := range c.CourseFile.Releases {
		err = c.cloneGitRepo(release)
		if err != nil {
			color.Red(err.Error())
		}

		out, err := c.TemplateRelease(release.Name)
		if err != nil {
			color.Red(err.Error())
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
	args, tmpFile, err := buildHelmArgs("template", c.BaseDirectory, *c.CourseFile.Releases[releaseIndex], c.CourseFile.HelmArgs)
	if err != nil {
		return "", err
	}
	if tmpFile != nil {
		defer os.Remove(tmpFile.Name())
	}
	out, stdErr, err := c.Helm.Exec(args...)
	if err != nil {
		return "", fmt.Errorf("error templating release %s: %s", releaseName, stdErr)
	}

	if len(c.OutputDirectory) > 0 {
		err = c.WriteSplitYaml([]byte(out), c.OutputDirectory, releaseName)
		if err != nil {
			color.Red(err.Error())
			os.Exit(1)
		}
	}

	// if the user has specified a RepoURL, they probably also
	// specified other things. Most required things receive a default
	// and a warning when not found in the config file. This
	// maybe could use some improvement
	if c.CourseFile.GitOps.ArgoCD.Spec.Source.RepoURL != "" && c.OutputDirectory != "" {
		err = c.WriteArgoApplications(c.OutputDirectory)
		if err != nil {
			color.Red(err.Error())
			os.Exit(1)
		}
	}

	return out, nil
}

// buildHelmArgs creates a helm command from a release
// takes a command either "upgrade" or "template"
// also returns the temp file of the values file to close
// NOTE: The order is really important here
func buildHelmArgs(command, baseDir string, release course.Release, additionalArgs []string) ([]string, *os.File, error) {
	var valuesFile *os.File
	var args []string
	switch command {
	case "upgrade":
		args = []string{"upgrade", "--install"}
	case "template":
		args = []string{"template"}
	}

	if len(additionalArgs) > 0 {
		args = append(args, additionalArgs...)
	}

	args = append(args, release.Name)
	if release.GitClonePath != nil {
		args = append(args, fmt.Sprintf("%s/%s", *release.GitClonePath, *release.GitChartSubPath))
	} else {
		args = append(args, fmt.Sprintf("%s/%s", release.Repository, release.Chart))
	}

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

	args = append(args, filesArgs(release.Files, baseDir)...)

	args = append(args, fmt.Sprintf("--namespace=%s", release.Namespace))

	if release.Version != "" && release.GitClonePath == nil {
		args = append(args, fmt.Sprintf("--version=%s", release.Version))
	}

	return args, valuesFile, nil
}

func filesArgs(files []string, baseDir string) []string {
	var args []string
	for _, file := range files {
		if file[0] == '/' {
			args = append(args, fmt.Sprintf("--values=%s", file))
		} else {
			args = append(args, fmt.Sprintf("--values=%s/%s", baseDir, file))
		}
	}
	return args
}

// makeTempValuesFile puts the values section into a temporary values file
func makeTempValuesFile(values map[string]interface{}) (*os.File, error) {
	tmpFile, err := os.CreateTemp(os.TempDir(), "reckoner-")
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

func (c *Client) cloneGitRepo(release *course.Release) error {
	if release.GitClonePath != nil {
		if err := c.cloneGitRepository(release); err != nil {
			color.Red("error with release %s: %s, continuing.", release.Name, err.Error())
			return err
		}

		if err := c.Helm.BuildDependencies(fmt.Sprintf("%s/%s", *release.GitClonePath, *release.GitChartSubPath)); err != nil {

			color.Red("error with release %s: %s, continuing.", release.Name, err.Error())
			return err
		}
	}
	return nil
}
