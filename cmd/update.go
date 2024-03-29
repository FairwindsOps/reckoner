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
	"os"

	"github.com/blang/semver"
	"github.com/gookit/color"
	"github.com/rhysd/go-github-selfupdate/selfupdate"
	"github.com/spf13/cobra"
	"k8s.io/klog/v2"
)

var updateReckonerCmd = &cobra.Command{
	Use:   "update-cli",
	Short: "Update reckoner.",
	Long:  "Updates the reckoner binary to the latest tagged release.",
	Run: func(cmd *cobra.Command, args []string) {
		klog.V(4).Infof("current version: %s", version)
		v, err := semver.Parse(version)
		if err != nil {
			color.Red.Printf("Could not parse version: %s\n", err.Error())
			os.Exit(1)
		}
		color.Green.Printf("Checking for update. Current version: %s\n", version)

		up, err := selfupdate.NewUpdater(selfupdate.Config{})
		if err != nil {
			color.Red.Println(err)
			os.Exit(1)
		}
		latest, err := up.UpdateSelf(v, "fairwindsops/reckoner")
		if err != nil {
			color.Red.Println("Update failed:", err)
			os.Exit(1)
		}
		if latest.Version.Equals(v) {
			color.Green.Println("Current binary is the latest version", version)
		} else {
			color.Green.Println("Successfully updated to version", latest.Version)
			color.Gray.Println("Release note:\n", latest.ReleaseNotes)
		}
	},
}
