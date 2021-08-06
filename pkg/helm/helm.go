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

package helm

import (
	"bytes"
	"fmt"
	"os/exec"

	"github.com/Masterminds/semver"
	"k8s.io/klog"
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
		return "", "", fmt.Errorf("exit code %d running command %s", cmd.ProcessState.ExitCode(), cmd.String())
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
