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
	"flag"
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"github.com/spf13/pflag"
	"gopkg.in/yaml.v3"
	"k8s.io/klog"

	"github.com/fairwindsops/reckoner/pkg/course"
	"github.com/fairwindsops/reckoner/pkg/reckoner"
)

var (
	version       string
	versionCommit string

	//runAll contains the boolean flag to install all the releases
	runAll bool
	//courseFile is the name and path of the course.yml file
	courseFile string
	//onlyRun contains the list of releases to install
	onlyRun []string
)

func init() {
	rootCmd.PersistentFlags().BoolVarP(&runAll, "run-all", "a", false, "Install every release in the course file")
	rootCmd.PersistentFlags().StringSliceVarP(&onlyRun, "only", "o", nil, "Only install this list of releases. Can be passed multiple times.")

	// add commands here
	rootCmd.AddCommand(plotCmd)
	rootCmd.AddCommand(convertCmd)
	rootCmd.AddCommand(templateCmd)
	rootCmd.AddCommand(diffCmd)
	rootCmd.AddCommand(lintCmd)

	klog.InitFlags(nil)
	flag.Parse()
	pflag.CommandLine.AddGoFlagSet(flag.CommandLine)
}

var rootCmd = &cobra.Command{
	Use:   "reckoner",
	Short: "reckoner",
	Long:  `A tool to maintain your helm installations as code.`,
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("You must specify a sub-command.")
		err := cmd.Help()
		if err != nil {
			klog.Error(err)
		}
		os.Exit(1)
	},
}

var plotCmd = &cobra.Command{
	Use:   "plot",
	Short: "plot <course file>",
	Long:  "Runs a helm install on a release or several releases.",
	Run: func(cmd *cobra.Command, args []string) {
		// TODO: Call Plot
	},
}

var templateCmd = &cobra.Command{
	Use:     "template",
	Short:   "template <course file>",
	Long:    "Templates a helm chart for a release or several releases.",
	PreRunE: validateCourseFileArg,
	Run: func(cmd *cobra.Command, args []string) {
		// TODO: This is just a stub
		client, err := reckoner.NewClient(courseFile, runAll, onlyRun, false)
		if err != nil {
			klog.Fatal(err)
		}
		tmpl, err := client.Template()
		if err != nil {
			klog.Fatal(err)
		}
		fmt.Println(tmpl)
	},
}

var diffCmd = &cobra.Command{
	Use:   "diff",
	Short: "diff <course file>",
	Long:  "Diffs the currently defined release and the one in the cluster",
	Run: func(cmd *cobra.Command, args []string) {
		// TODO: Call Diff
	},
}

var lintCmd = &cobra.Command{
	Use:   "lint",
	Short: "lint <course file>",
	Long:  "Lints the course file. Checks for structure and valid yaml.",
	Run: func(cmd *cobra.Command, args []string) {
		// TODO: Call Lint
	},
}

var convertCmd = &cobra.Command{
	Use:     "convert",
	Short:   "convert <course file> from v1 to v2 schema",
	Long:    "Converts a course file from the v1 python schema to v2 go schema",
	PreRunE: validateCourseFileArg,
	Run: func(cmd *cobra.Command, args []string) {
		newCourse, err := course.ConvertV1toV2(courseFile)
		if err != nil {
			klog.Fatal(err)
		}
		// We prefer 2 spaces in yaml
		w := os.Stdout
		e := yaml.NewEncoder(w)
		defer e.Close()
		e.SetIndent(2)

		err = e.Encode(newCourse)
		if err != nil {
			klog.Fatal(err)
		}
	},
}

// validateCourseFileArg ensures that the only argument passed is a course
// file that exists
func validateCourseFileArg(cmd *cobra.Command, args []string) error {
	if len(args) != 1 {
		return fmt.Errorf("you must pass a single course file argument")
	}

	_, err := os.Stat(args[0])
	if os.IsNotExist(err) {
		return fmt.Errorf("specified course file %s does not exist", args[0])
	}
	courseFile = args[0]
	return nil
}

// Execute the stuff
func Execute(VERSION string, COMMIT string) {
	version = VERSION
	versionCommit = COMMIT
	if err := rootCmd.Execute(); err != nil {
		klog.Error(err)
		os.Exit(1)
	}
}
