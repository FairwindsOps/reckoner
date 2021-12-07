package reckoner

import (
	"strings"

	"github.com/fatih/color"
)

func (c *Client) GetManifests() (string, error) {
	var fullOutput string
	for _, release := range c.CourseFile.Releases {
		manifests, err := c.Helm.GetManifest(release.Namespace, release.Name)
		if err != nil {
			color.Yellow("Failed to get manifests for %s: %s", release.Name, err)
		}
		fullOutput = fullOutput + manifests
	}
	return strings.TrimSuffix(fullOutput, "\n"), nil
}
