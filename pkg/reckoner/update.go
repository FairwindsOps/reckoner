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
	"github.com/fairwindsops/reckoner/pkg/course"
	"github.com/fatih/color"
)

func (c *Client) Update() error {
	updatedReleases := []*course.Release{}
	for i, release := range c.CourseFile.Releases {
		thisReleaseDiff, err := c.diffRelease(release.Name, release.Namespace)
		if err != nil {
			if c.Continue() {
				color.Red("error with release %s: %s, continuing.", release.Name, err.Error())
				continue
			}
			return err
		}
		if thisReleaseDiff != "" {
			color.Yellow("Update available for %s in namespace %s. Added to plot list.", release.Name, release.Namespace)
			updatedReleases = append(updatedReleases, c.CourseFile.Releases[i])
			continue
		}
		color.Green("No update necessary for %s in namespace %s.", release.Name, release.Namespace)
	}
	c.CourseFile.Releases = updatedReleases
	err := c.Plot()
	if err != nil {
		return err
	}
	return nil
}
