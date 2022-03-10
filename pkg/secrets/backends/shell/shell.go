package shell

import (
	"bytes"
	"fmt"
	"os/exec"

	"github.com/pkg/errors"
	"k8s.io/klog/v2"
)

// Executor represents a shell script to run
type Executor struct {
	Executable string
	Args       []string
}

// NewExecutor returns a shell.Executor with the given script
func NewExecutor(script []string) (*Executor, error) {
	var args []string
	if len(script) == 1 {
		args = []string{}
	} else {
		args = script[1:]
	}
	path, err := exec.LookPath(script[0])
	if err != nil {
		return nil, errors.Wrap(err, fmt.Sprintf("failed to find executable for ShellExecutor secret: %s", script[0]))
	}
	return &Executor{
		Executable: path,
		Args:       args,
	}, nil
}

func (s Executor) Get(key string) (string, error) {
	cmd := exec.Command(s.Executable, s.Args...)
	var stdoutBuf, stderrBuf bytes.Buffer

	cmd.Stdout = &stdoutBuf
	cmd.Stderr = &stderrBuf

	err := cmd.Run()
	outStr, errStr := stdoutBuf.String(), stderrBuf.String()
	if err != nil {
		klog.V(8).Infof("stdout: %s", outStr)
		klog.V(7).Infof("stderr: %s", errStr)
		return "", errors.Wrap(err, fmt.Sprintf("exit code %d running command %s", cmd.ProcessState.ExitCode(), cmd.String()))
	}
	return outStr, nil
}
