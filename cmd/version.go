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

package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
)

var (
	shortVersion bool
)

func init() {
	versionCmd.PersistentFlags().BoolVar(&shortVersion, "short", false, "Display only the version. Useful for automation")
}

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Prints the current version of the tool.",
	Long:  `Prints the current version.`,
	Run: func(cmd *cobra.Command, args []string) {
		if shortVersion {
			fmt.Println(version)
		} else {
			fmt.Println("Version:" + version + " Commit:" + versionCommit)
		}
	},
}
