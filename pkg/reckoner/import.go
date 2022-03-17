package reckoner

import (
	"bytes"
	"fmt"
	"strings"

	"github.com/Masterminds/semver/v3"
	"github.com/fairwindsops/reckoner/pkg/course"
	"github.com/fairwindsops/reckoner/pkg/helm"
	"gopkg.in/yaml.v3"
)

type ImportInfo struct {
	Chart     string
	Version   string
	Name      string
	Namespace string
}

type ImportValues map[string]interface{}

func ImportOutput(release, namespace, repository string) (string, error) {
	helmClient, err := helm.NewClient()
	if err != nil {
		return "", err
	}
	releaseInfo, err := gatherReleaseInfo(helmClient, namespace, release)
	if err != nil {
		return "", err
	}
	if err := releaseInfo.parseChartVersion(); err != nil {
		return "", err
	}
	userValues, err := gatherUserSuppliedValues(helmClient, namespace, release)
	if err != nil {
		return "", err
	}

	// set up and populate a release struct that will be used to output in yaml format
	var releaseOut = new(course.Release)
	releaseOut.Name = releaseInfo.Name
	releaseOut.Namespace = releaseInfo.Namespace
	releaseOut.Chart = releaseInfo.Chart
	releaseOut.Version = releaseInfo.Version
	releaseOut.Values = userValues
	releaseOut.Repository = repository

	// in order to set indent to 2 spaces we need to use a yaml encoder instead of yaml.Marshal
	ret := bytes.NewBuffer([]byte{})
	encoder := yaml.NewEncoder(ret)
	defer encoder.Close()
	encoder.SetIndent(2)
	if err := encoder.Encode(releaseOut); err != nil {
		return "", err
	}

	return ret.String(), err
}

func gatherReleaseInfo(helmClient *helm.Client, namespace, release string) (*ImportInfo, error) {
	var allReleases = new([]*ImportInfo)
	releaseInfo, err := helmClient.ListNamespaceReleasesYAML(namespace)
	if err != nil {
		return nil, err
	}
	if err := yaml.Unmarshal(releaseInfo, allReleases); err != nil {
		return nil, err
	}
	for _, r := range *allReleases {
		if r.Name == release {
			return r, nil
		}
	}
	return nil, fmt.Errorf("could not find release %s in namespace %s", release, namespace)
}

func gatherUserSuppliedValues(helmClient *helm.Client, namespace, release string) (ImportValues, error) {
	var values = make(ImportValues)
	userValues, err := helmClient.GetUserSuppliedValuesYAML(namespace, release)
	if err != nil {
		return nil, err
	}
	if err := yaml.Unmarshal(userValues, values); err != nil {
		return nil, err
	}
	return values, nil
}

func (i *ImportInfo) parseChartVersion() error {
	splitChartVersion := strings.Split(i.Chart, "-")
	if len(splitChartVersion) < 2 {
		return fmt.Errorf("could not parse chart version from %s - expected at least one hyphen between chart name and version", i.Chart)
	}
	splitPoint := len(splitChartVersion) - 1
	i.Chart = strings.Join(splitChartVersion[:splitPoint], "-")
	i.Version = splitChartVersion[splitPoint]
	if _, err := semver.NewVersion(i.Version); err != nil {
		return fmt.Errorf("go %s as version string which is not valid semver", i.Version)
	}
	return nil
}
