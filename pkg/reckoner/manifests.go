package reckoner

import (
	"bytes"
	"fmt"
	"io"
	"regexp"
	"strings"

	"github.com/fatih/color"
	"gopkg.in/yaml.v3"
)

// Manifest represents a single kubernetes yaml manifest from a helm release. It could be from a 'template' command or 'get' command.
type Manifest struct {
	Source   string
	Kind     string
	Metadata Metadata
	Content  string
}

// Metadata only includes a Name field for a given resource.
type Metadata struct {
	Name string
}

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

// ManifestUnmarshal converts a manifest string that includes all resources from a chart
// and breaks them up into their individual resource manifests.
//
// Returns a slice of Manifest structs.
func ManifestUnmarshal(in string) ([]Manifest, error) {
	var manifests []Manifest
	dec := yaml.NewDecoder(bytes.NewReader([]byte(in)))
	for {
		var manifest Manifest
		err := dec.Decode(&manifest)
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, err
		}
		manifests = append(manifests, manifest)
	}
	return manifests, nil
}

// UnmarshalYAML satisfies the yaml.Unmarshaler interface for a Manifest object.
// This ensures that a manifest object can properly pull the Source, Kind, and Metadata fields
// and then populates the contents field with the raw yaml, not including the Source comment.
func (m *Manifest) UnmarshalYAML(value *yaml.Node) error {
	if value.Kind != yaml.MappingNode {
		return fmt.Errorf("Manifest must contain YAML mapping, has %v", value.Kind)
	}
	for i := 0; i < len(value.Content); i += 2 {
		commentRe := regexp.MustCompile(`^# Source: (.*)$`)
		matchedComment := commentRe.FindStringSubmatch(value.Content[i].HeadComment)
		if len(matchedComment) > 0 {
			m.Source = matchedComment[1]
		}
		switch value.Content[i].Value {
		case "kind":
			if err := value.Content[i+1].Decode(&m.Kind); err != nil {
				return err
			}
		case "metadata":
			if err := value.Content[i+1].Decode(&m.Metadata); err != nil {
				return err
			}
		}
	}
	content := map[string]interface{}{}
	if err := value.Decode(&content); err != nil {
		return err
	}
	contentBytes, err := yaml.Marshal(content)
	if err != nil {
		return err
	}
	m.Content = string(contentBytes)
	return nil
}
