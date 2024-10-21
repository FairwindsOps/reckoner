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

package helm

import (
	"bytes"
	"errors"
	"fmt"
	"os/exec"
	"strings"

	"github.com/Masterminds/semver/v3"
	"github.com/thoas/go-funk"
	"k8s.io/klog/v2"
)

// Client is a local helm client
type Client struct {
	HelmExecutable string
}

// NewClient ensures a helm command exists
func NewClient() (*Client, error) {
	path, err := exec.LookPath("helm")
	if err != nil {
		return nil, fmt.Errorf("helm must be installed and available in path: %s", err.Error())
	}
	klog.V(3).Infof("found helm at %s", path)
	return &Client{path}, nil
}

// Exec returns the output and error of a helm command given several arguments
// Returns stdOut and stdErr as well as any error
func (h Client) Exec(arg ...string) (string, string, error) {
	cmd := exec.Command(h.HelmExecutable, arg...)

	klog.V(8).Infof("running helm command: %v", cmd)

	var stdoutBuf, stderrBuf bytes.Buffer

	cmd.Stdout = &stdoutBuf
	cmd.Stderr = &stderrBuf

	err := cmd.Run()
	outStr, errStr := stdoutBuf.String(), stderrBuf.String()
	if err != nil {
		klog.V(8).Infof("stdout: %s", outStr)
		klog.V(7).Infof("stderr: %s", errStr)
		return "", errStr, fmt.Errorf("exit code %d running command %s", cmd.ProcessState.ExitCode(), cmd.String())
	}

	return outStr, errStr, nil
}

// Version returns the helm client version
func (h Client) Version() (*semver.Version, error) {
	out, _, err := h.Exec("version", "--template={{.Version}}")
	if err != nil {
		return nil, err
	}
	version, err := semver.NewVersion(out)
	if err != nil {
		return nil, err
	}
	return version, nil
}

// AddRepository adds a Helm repository
func (h Client) AddRepository(repoName, url string) error {
	_, _, err := h.Exec("repo", "add", repoName, url)
	if err != nil {
		return err
	}

	return nil
}

// Cache returns the local helm cache if defined
func (h Client) Cache() (string, error) {
	stdOut, stdErr, err := h.Exec("env")
	if err != nil {
		return "", fmt.Errorf("error running helm env: %s", stdErr)
	}
	for _, line := range strings.Split(stdOut, "\n") {
		if strings.Contains(line, "HELM_REPOSITORY_CACHE") {
			value := strings.Split(line, "=")[1]
			return strings.Trim(value, "\""), nil
		}
	}
	return "", fmt.Errorf("could not find HELM_REPOSITORY_CACHE in helm env output")
}

// BuildDependencies will update dependencies for a given release if it is stored locally (i.e. pulled from git)
func (h Client) BuildDependencies(path string) error {
	klog.V(5).Infof("building chart dependencies for %s", path)
	_, stdErr, err := h.Exec("dependency", "build", path)
	if err != nil {
		return fmt.Errorf("error running helm dependency build: %s", stdErr)
	}

	return nil
}

// GetManifestString will run 'helm get manifest' on a given namespace and release and return string output.
func (h Client) GetManifestString(namespace, release string) (string, error) {
	out, err := h.get("manifest", namespace, release)
	if err != nil {
		return "", err
	}
	return out, err
}

// GetUserSuppliedValues will run 'helm get values' on a given namespace and release and return []byte output suitable for yaml Marshaling.
func (h Client) GetUserSuppliedValuesYAML(namespace, release string) ([]byte, error) {
	out, err := h.get("values", namespace, release, "--output", "yaml")
	if err != nil {
		return nil, err
	}
	return []byte(out), err
}

// ListNamespaceReleasesYAML will run 'helm list' on a given namespace and return []byte output suitable for yaml Marshaling.
func (h Client) ListNamespaceReleasesYAML(namespace string) ([]byte, error) {
	out, err := h.list(namespace, "--output", "yaml")
	if err != nil {
		return nil, err
	}
	return []byte(out), nil
}

// get can run any 'helm get' command
func (h Client) get(kind, namespace, release string, extraArgs ...string) (string, error) {
	validKinds := []string{"all", "hooks", "manifest", "notes", "values"}
	if !funk.Contains(validKinds, kind) {
		return "", errors.New("invalid kind passed to helm: " + kind)
	}
	args := []string{"get", kind, "--namespace", namespace, release}
	args = append(args, extraArgs...)
	stdOut, stdErr, err := h.Exec(args...)
	if err != nil && stdErr != "" {
		return "", errors.New(stdErr)
	}
	return stdOut, nil
}

// list can run any 'helm list' command
func (h Client) list(namespace string, extraArgs ...string) (string, error) {
	args := []string{"list", "--namespace", namespace}
	args = append(args, extraArgs...)
	stdOut, stdErr, err := h.Exec(args...)
	if err != nil && stdErr != "" {
		return "", errors.New(stdErr)
	}
	return stdOut, nil
}
