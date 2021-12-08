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

package reckoner

import (
	"fmt"
	"os"
)

// ValidateArgs validates that the correct arguments were passed and returns the name of the course file
func ValidateArgs(runAll bool, onlyRun, args []string) (string, error) {
	if runAll && len(onlyRun) != 0 {
		return "", fmt.Errorf("you must either use run-all or only")
	}

	if !runAll && len(onlyRun) == 0 {
		return "", fmt.Errorf("you must use at least one of run-all or only")
	}

	if len(args) != 1 {
		return "", fmt.Errorf("you must pass a single course file argument")
	}

	_, err := os.Stat(args[0])
	if os.IsNotExist(err) {
		return "", fmt.Errorf("specified course file %s does not exist", args[0])
	}
	return args[0], err
}
