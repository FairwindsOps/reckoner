package reckoner

import (
	"os/exec"
	"strings"

	"k8s.io/klog"
)

func execHook(hooks []string) error {
	if len(hooks) == 0 {
		return nil
	}


	
	for _, hook := range hooks {
		klog.Infof("Running hook %s", hook)
		cmds := strings.Split(hook, " ")
		args := cmds[1:]

		// TODO: take baseDirectory into consideration
		cmd := exec.Command(cmds[0], args...)


		data, runError := cmd.CombinedOutput()
		klog.V(3).Infof("command %s output: %s", cmd.String(), string(data))
		if runError != nil {
			return runError
		}
		

	}
	return nil
}
