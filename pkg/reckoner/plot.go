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
	"errors"
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"regexp"
	"strings"

	"gopkg.in/yaml.v3"
	"k8s.io/klog"

	"github.com/fairwindsops/reckoner/pkg/course"
	"github.com/fatih/color"
	git "github.com/go-git/go-git/v5"
	"github.com/go-git/go-git/v5/plumbing"
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

		if c.CourseFile.Repositories[release.Repository].Git != "" {
			if err := c.cloneGitRepository(release); err != nil {
				return err
			}
		}

		args, tmpFile, err := buildHelmArgs("upgrade", *release)
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
	args, tmpFile, err := buildHelmArgs("template", *c.CourseFile.Releases[releaseIndex])
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

func (c Client) cloneGitRepository(release *course.Release) error {
	releaseRepository := c.CourseFile.Repositories[release.Repository]
	if release.Version == "" {
		release.Version = "master"
	}
	cacheDir, err := c.Helm.Cache()
	if err != nil {
		return err
	}
	re := regexp.MustCompile(`\:\/\/|\/|\.`)
	subPath := re.ReplaceAllString(releaseRepository.Git, "_")
	clonePath := fmt.Sprintf("%s/%s_goreckoner", cacheDir, subPath)

	err = release.SetGitClonePath(fmt.Sprintf("%s/%s", clonePath, releaseRepository.Path))
	if err != nil {
		return err
	}

	repo, worktree, err := setupGitRepoPath(clonePath, releaseRepository.Git)
	if err != nil {
		return err
	}

	err = repo.Fetch(&git.FetchOptions{
		Tags: git.AllTags,
	})
	if err != nil && !errors.Is(err, git.NoErrAlreadyUpToDate) {
		return fmt.Errorf("Error fetching git repository %s - %s", clonePath, err)
	}

	hash, err := repo.ResolveRevision(plumbing.Revision(release.Version))
	if errors.Is(err, plumbing.ErrReferenceNotFound) {
		hash, err = repo.ResolveRevision(plumbing.Revision(fmt.Sprintf("origin/%s", release.Version)))
	}
	if err != nil {
		return fmt.Errorf("Error resolving git revision %s - %s", release.Version, err)
	}

	err = worktree.Checkout(&git.CheckoutOptions{
		Hash: *hash,
	})
	if err != nil {
		return fmt.Errorf("Error checking out git repository %s - %s", clonePath, err)
	}

	return nil
}

// buildHelmArgs creates a helm command from a release
// takes a command either "upgrade" or "template"
// also returns the temp file of the values file to close
// NOTE: The order is really important here
func buildHelmArgs(command string, release course.Release) ([]string, *os.File, error) {
	var valuesFile *os.File
	var args []string
	switch command {
	case "upgrade":
		args = []string{"upgrade", "--install"}
	case "template":
		args = []string{"template"}
	}

	args = append(args, release.Name)
	useGit, gitPath := release.GitClonePath()
	if useGit {
		args = append(args, gitPath)
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

	if len(release.Files) > 0 {
		for _, file := range release.Files {
			args = append(args, fmt.Sprintf("--values=%s", file))
		}
	}

	args = append(args, fmt.Sprintf("--namespace=%s", release.Namespace))

	if release.Version != "" && !useGit {
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

func setupGitRepoPath(clonePath, url string) (*git.Repository, *git.Worktree, error) {
	var repo *git.Repository
	var worktree *git.Worktree
	if _, err := os.Stat(clonePath); errors.Is(err, os.ErrNotExist) {
		err := os.Mkdir(clonePath, 0755)
		if err != nil {
			return nil, nil, fmt.Errorf("Error creating directory %s - %s", clonePath, err)
		}
	}
	if empty, err := dirIsEmpty(clonePath); empty && err == nil {
		repo, err := git.PlainClone(clonePath, false, &git.CloneOptions{
			URL: url,
		})
		if err != nil {
			return nil, nil, fmt.Errorf("Error initializing git repository %s - %s", clonePath, err)
		}
		worktree, err = repo.Worktree()
		if err != nil {
			return nil, nil, fmt.Errorf("Error getting git working tree %s - %s", clonePath, err)
		}
	} else {
		if err != nil {
			return nil, nil, fmt.Errorf("Error checking if directory is empty %s - %s", clonePath, err)
		}
		repo, err = git.PlainOpen(clonePath)
		if errors.Is(err, git.ErrRepositoryNotExists) {
			err := os.RemoveAll(clonePath)
			if err != nil {
				return nil, nil, fmt.Errorf("Error removing directory %s - %s", clonePath, err)
			}
			err = os.MkdirAll(clonePath, 0755)
			if err != nil {
				return nil, nil, fmt.Errorf("Error creating directory %s - %s", clonePath, err)
			}
			repo, err = git.PlainClone(clonePath, false, &git.CloneOptions{
				URL: url,
			})
			if err != nil {
				return nil, nil, fmt.Errorf("Error initializing git repository %s - %s", clonePath, err)
			}
		} else if err != nil {
			return nil, nil, fmt.Errorf("Error opening git repository %s - %s", clonePath, err)
		}
		worktree, err = repo.Worktree()
		if err != nil {
			return nil, nil, fmt.Errorf("Error getting git working tree %s - %s", clonePath, err)
		}
	}
	return repo, worktree, nil
}

func dirIsEmpty(name string) (bool, error) {
	f, err := os.Open(name)
	if err != nil {
		return false, err
	}
	defer f.Close()

	_, err = f.Readdirnames(1)
	if errors.Is(err, io.EOF) {
		return true, nil
	}
	return false, err
}
