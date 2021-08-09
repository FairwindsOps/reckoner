package reckoner

import (
	"os/exec"
	"strings"

	"k8s.io/klog"
)

func (c Client) execHook(hooks []string) error {
	if c.DryRun {
		klog.Warningf("hook not run due to --dry-run: %v", c.DryRun)
		return nil
	}

	if len(hooks) == 0 {
		return nil
	}

	for _, hook := range hooks {
		klog.Infof("Running hook %s", hook)
		commands := strings.Split(hook, " ")
		args := commands[1:]

		command := exec.Command(commands[0], args...)
		command.Dir = c.BaseDirectory

		data, runError := command.CombinedOutput()
		klog.V(3).Infof("command %s output: %s", command.String(), string(data))
		if runError != nil {
			return runError
		}

	}
	return nil
}
