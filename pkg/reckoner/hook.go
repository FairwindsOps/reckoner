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

package reckoner

import (
	"os/exec"
	"strings"

	"github.com/fatih/color"
)

func (c Client) execHook(hooks []string, kind string) error {
	if c.DryRun {
		color.Yellow("hook not run due to --dry-run: %v", c.DryRun)
		return nil
	}

	if len(hooks) == 0 {
		return nil
	}

	for _, hook := range hooks {
		color.Green("Running %s hook: %s", kind, hook)
		commands := strings.Split(hook, " ")
		args := commands[1:]

		command := exec.Command(commands[0], args...)
		command.Dir = c.BaseDirectory

		data, runError := command.CombinedOutput()
		color.Green("Hook '%s' output: %s", command.String(), string(data))
		if runError != nil {
			return runError
		}

	}
	return nil
}
