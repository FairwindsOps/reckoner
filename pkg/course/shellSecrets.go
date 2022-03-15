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
