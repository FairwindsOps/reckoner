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
	"bytes"
	"fmt"
	"strings"

	"github.com/fatih/color"
	"github.com/sergi/go-diff/diffmatchpatch"
	"github.com/thoas/go-funk"
)

// ManifestDiff is a struct that contains the diff between a manifest (from 'helm get manifest') and a template (from 'helm template')
// The fields help identify the which resource is being diffed from the helm chart.
type ManifestDiff struct {
	ReleaseName string
	Kind        string
	Name        string
	Source      string
	Diff        string
	NewFile     bool
}

// String returns a string representation of the ManifestDiff
func (md ManifestDiff) String() string {
	if md.Diff == "" {
		return ""
	}
	preDiff := ""
	if md.NewFile {
		preDiff = " does not exist and will be added\n"
	}
	return fmt.Sprintf("\n%s \"%s\"%s\n%s", md.Kind, md.Name, preDiff, md.Diff)
}

// Diff gathers a given release's manifest and templates and outputs a string of diffs if there are any or reports that there are no diffs.
func (c *Client) Diff() error {
	for _, release := range c.CourseFile.Releases {
		fmt.Printf("\nRunning 'diff' on %s in %s\n", release.Name, release.Namespace)
		thisReleaseDiff, err := c.diffRelease(release.Name, release.Namespace)
		if err != nil {
			if c.Continue() {
				color.Red("error with release %s: %s, continuing.", release.Name, err.Error())
				continue
			}
			return err
		}
		if thisReleaseDiff == "" {
			color.Green("There are no differences in release %s", release.Name)
		} else {
			fmt.Print(thisReleaseDiff)
		}
	}
	return nil
}

func (c *Client) diffRelease(releaseName, releaseNamespace string) (string, error) {
	manifests, err := c.Helm.GetManifestString(releaseNamespace, releaseName)
	if err != nil && err.Error() == "Error: release: not found\n" {
		manifests = ""
	} else if err != nil {
		return "", fmt.Errorf("error getting manifests for release %s in namespace %s: %s", releaseName, releaseNamespace, err)
	}
	templateOut, err := c.TemplateRelease(releaseName)
	if err != nil {
		return "", fmt.Errorf("error getting template for release %s in namespace %s: %s", releaseName, releaseNamespace, err)
	}
	manifestSlice, err := ManifestUnmarshal(manifests)
	if err != nil {
		return "", err
	}
	templateSlice, err := ManifestUnmarshal(templateOut)
	if err != nil {
		return "", err
	}
	diffs, err := populateDiffs(releaseName, manifestSlice, templateSlice)
	if err != nil {
		return "", err
	}
	thisReleaseDiff := ""
	for _, diff := range diffs {
		thisReleaseDiff += diff.String()
	}
	return thisReleaseDiff, nil
}

// poulateDiffs takes a specific release and diffs the manifests and templates. If the given release taken from the coursefile does
// not exist in the cluster, we return a diff compared to an empty string so that we get the full output of the template.
func populateDiffs(releaseName string, manifestSlice, templateSlice []Manifest) ([]ManifestDiff, error) {
	diffs := []ManifestDiff{}
	for _, template := range templateSlice {
		found := funk.Contains(manifestSlice, func(manifest Manifest) bool {
			return template.Metadata.Name == manifest.Metadata.Name && template.Kind == manifest.Kind && template.Source == manifest.Source
		})
		diffString := ""
		thisDiff := &ManifestDiff{}
		switch found {
		case true:
			manifestIndex := funk.IndexOf(manifestSlice, func(manifest Manifest) bool {
				return template.Metadata.Name == manifest.Metadata.Name && template.Kind == manifest.Kind && template.Source == manifest.Source
			})
			diffString = diffReleaseManifests(manifestSlice[manifestIndex].Content, template.Content)
		case false:
			diffString = diffReleaseManifests("", template.Content)
			thisDiff.NewFile = true
		}
		thisDiff.ReleaseName = releaseName
		thisDiff.Kind = template.Kind
		thisDiff.Name = template.Metadata.Name
		thisDiff.Source = template.Source
		thisDiff.Diff = diffString
		thisDiff.properColor()
		diffs = append(diffs, *thisDiff)
	}
	return diffs, nil
}

// diffReleaseManifests takes two strings and returns the diff between them. It also adds in up to 4 lines of context around a diff (before and after), if available.
func diffReleaseManifests(old, new string) string {
	dmp := diffmatchpatch.New()
	wSrc, wDst, warray := dmp.DiffLinesToRunes(old, new)
	diffs := dmp.DiffMainRunes(wSrc, wDst, true)
	diffs = dmp.DiffCharsToLines(diffs, warray)
	actualDiffs := []diffmatchpatch.Diff{}
	for i, d := range diffs {
		if d.Type == diffmatchpatch.DiffEqual {
			continue
		}
		if i > 0 && diffs[i-1].Type == diffmatchpatch.DiffEqual {
			text := strings.Split(diffs[i-1].Text, "\n")
			context := 4
			if len(text)-1 < context {
				context = len(text) - 1
			}
			beforeContext := text[len(text)-context:]
			beforeContext[0] = "\n" + beforeContext[0]
			actualDiffs = append(actualDiffs, diffmatchpatch.Diff{Type: diffmatchpatch.DiffEqual, Text: strings.Join(beforeContext, "\n")})
		}
		formatDiffLines(&d)
		actualDiffs = append(actualDiffs, d)
		if i < len(diffs)-1 && diffs[i+1].Type == diffmatchpatch.DiffEqual {
			text := strings.Split(diffs[i+1].Text, "\n")
			context := 4
			if len(text)-1 < context {
				context = len(text) - 1
			}
			joinedText := strings.Join(text[:context], "\n") + "\n"
			actualDiffs = append(actualDiffs, diffmatchpatch.Diff{Type: diffmatchpatch.DiffEqual, Text: joinedText})
		}
	}
	return dmp.DiffPrettyText(actualDiffs)
}

// formatDiffLines adds '+' in front of any DiffInsert diff lines, and '-' in front of any DiffDelete diff lines.
// By default, diffmatchpatch only colorizes diffs, but we need to see the identifiers if color is not available.
func formatDiffLines(diff *diffmatchpatch.Diff) {
	var buff bytes.Buffer
	textSplit := strings.Split(diff.Text, "\n")
	for i, line := range textSplit {
		if i == len(textSplit)-1 {
			continue
		}
		var l string
		if diff.Type == diffmatchpatch.DiffDelete {
			l = "-" + strings.TrimPrefix(line, " ")
		}
		if diff.Type == diffmatchpatch.DiffInsert {
			l = "+" + strings.TrimPrefix(line, " ")
		}
		_, _ = buff.WriteString(l + "\n")
	}
	diff.Text = buff.String()
}

// properColor removes any colored lines that the diffmatchpatch library adds and then uses the color package to color the lines instead.
// We do this so that the color package that's instantiated in the 'cmd' package can turn color on and off properly.
func (md *ManifestDiff) properColor() {
	if len(md.Diff) == 0 {
		return
	}
	md.Diff = strings.Replace(md.Diff, "\x1b[32m", "", -1)
	md.Diff = strings.Replace(md.Diff, "\x1b[31m", "", -1)
	md.Diff = strings.Replace(md.Diff, "\x1b[0m", "", -1)
	splitDiff := strings.Split(md.Diff, "\n")
	for i, line := range splitDiff {
		if strings.HasPrefix(line, "+") {
			splitDiff[i] = color.GreenString(line)
		}
		if strings.HasPrefix(line, "-") {
			splitDiff[i] = color.RedString(line)
		}
		if i == len(splitDiff)-1 {
			splitDiff[i] = line + "\n"
		}
	}
	md.Diff = strings.Join(splitDiff, "\n")
}
