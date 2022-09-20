// Copyright 2022 Fairwinds
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
	"os"

	"github.com/fairwindsops/reckoner/pkg/course"
	"github.com/fatih/color"
	git "github.com/go-git/go-git/v5"
	"github.com/go-git/go-git/v5/plumbing"
)

func (c Client) cloneGitRepository(release *course.Release) error {
	releaseRepository := c.CourseFile.Repositories[release.Repository]
	if release.Version == "" {
		color.Yellow("Git repository in use with no version specified. Defaulting to master branch. This default will be removed in the future, please define a version for this release: %s", release.Name)
		release.Version = "master"
	}

	repo, worktree, err := setupGitRepoPath(*release.GitClonePath, releaseRepository.Git)
	if err != nil {
		return err
	}

	err = repo.Fetch(&git.FetchOptions{
		Tags: git.AllTags,
	})
	if err != nil && !errors.Is(err, git.NoErrAlreadyUpToDate) {
		return fmt.Errorf("Error fetching git repository %s - %s", *release.GitClonePath, err)
	}

	hash, err := determineGitRevisionHash(repo, release.Version)
	if err != nil {
		return err
	}

	err = worktree.Checkout(&git.CheckoutOptions{
		Hash:  *hash,
		Force: true,
	})
	if err != nil {
		return fmt.Errorf("Error checking out git repository %s - %s", *release.GitClonePath, err)
	}

	return nil
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
		repo, err = git.PlainClone(clonePath, false, &git.CloneOptions{
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

func determineGitRevisionHash(repo *git.Repository, version string) (*plumbing.Hash, error) {
	hash, err := repo.ResolveRevision(plumbing.Revision(version))
	if errors.Is(err, plumbing.ErrReferenceNotFound) {
		hash, err = repo.ResolveRevision(plumbing.Revision(fmt.Sprintf("origin/%s", version)))
	}
	if err != nil {
		return nil, fmt.Errorf("Error resolving git revision %s - %s", version, err)
	}
	return hash, nil
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
