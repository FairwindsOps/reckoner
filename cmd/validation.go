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

package cmd

import (
	"fmt"
	"os"

	"github.com/fatih/color"
	"github.com/spf13/cobra"
	"k8s.io/klog/v2"
)

// validateCobraArgs ensures that the only argument passed is a course
// file that exists
func validateCobraArgs(cmd *cobra.Command, args []string) (err error) {
	courseFile = getCourseFilePath(args) // guaranteed to return a path

	// at this point we should have a courseFile value. the following
	// makes sure the course file is accessible...
	err = validateCourseFilePath(courseFile)
	if err != nil {
		return err
	}

	// ...and checks that we passed the appropriate set of arguments
	err = validateArgs(runAll, onlyRun, args)
	if err != nil {
		return err
	}

	color.NoColor = noColor
	klog.V(3).Infof("colorize output: %v", !noColor)

	return err
}

// validateArgs validates that the correct arguments were passed and returns the name of the course file
func validateArgs(runAll bool, onlyRun, args []string) error {
	if runAll && len(onlyRun) != 0 {
		return fmt.Errorf("you must either use run-all or only")
	}

	if !runAll && len(onlyRun) == 0 {
		return fmt.Errorf("you must use at least one of run-all or only")
	}

	if len(args) > 1 {
		return fmt.Errorf("you may only pass one course YAML file at the same time")
	}

	return nil
}

func validateCourseFilePath(courseFile string) error {
	_, err := os.Stat(courseFile)
	if os.IsNotExist(err) {
		return fmt.Errorf("course file %s does not exist", courseFile)
	}
	return err
}
