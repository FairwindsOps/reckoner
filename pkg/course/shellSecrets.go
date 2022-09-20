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

package course

import (
	"bytes"
	"fmt"
	"os/exec"

	"k8s.io/klog/v2"
)

// Executor represents a shell script to run
type executor struct {
	Executable string
	Args       []string
}

// newShellExecutor returns an executor with the given script
func newShellExecutor(script []string) (*executor, error) {
	var args []string
	if len(script) == 1 {
		args = []string{}
	} else {
		args = script[1:]
	}
	path, err := exec.LookPath(script[0])
	if err != nil {
		return nil, fmt.Errorf("failed to find executable for ShellExecutor secret: %s - %w", script[0], err)
	}
	return &executor{
		Executable: path,
		Args:       args,
	}, nil
}

// Get returns the value of the secret and also satisfies the secrets.Getter interface
func (s executor) Get(key string) (string, error) {
	cmd := exec.Command(s.Executable, s.Args...)
	var stdoutBuf, stderrBuf bytes.Buffer

	cmd.Stdout = &stdoutBuf
	cmd.Stderr = &stderrBuf

	err := cmd.Run()
	outStr, errStr := stdoutBuf.String(), stderrBuf.String()
	if err != nil {
		klog.V(8).Infof("stdout: %s", outStr)
		klog.V(7).Infof("stderr: %s", errStr)
		return "", fmt.Errorf("exit code %d running command %s - %w", cmd.ProcessState.ExitCode(), cmd.String(), err)
	}
	return outStr, nil
}
