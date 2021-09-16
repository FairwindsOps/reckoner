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

	// runAll contains the boolean flag to install all the releases
	runAll bool
	// dryRun contains the boolean flag to run as dry run
	dryRun bool
	// courseFile is the name and path of the course.yml file
	courseFile string
	// onlyRun contains the list of releases to install
	onlyRun []string
)

func init() {
	rootCmd.PersistentFlags().BoolVarP(&runAll, "run-all", "a", false, "Install every release in the course file")
	rootCmd.PersistentFlags().StringSliceVarP(&onlyRun, "only", "o", nil, "Only install this list of releases. Can be passed multiple times.")
	rootCmd.PersistentFlags().BoolVar(&dryRun, "dry-run", false, "Implies helm --dry-run --debug and skips any hooks")

	// add commands here
	rootCmd.AddCommand(plotCmd)
	rootCmd.AddCommand(convertCmd)
	rootCmd.AddCommand(templateCmd)
	rootCmd.AddCommand(diffCmd)
	rootCmd.AddCommand(lintCmd)

	klog.InitFlags(nil)
	pflag.CommandLine.AddGoFlag(flag.CommandLine.Lookup("v"))
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
	Use:     "plot",
	Short:   "plot <course file>",
	Long:    "Runs a helm install on a release or several releases.",
	PreRunE: validateArgs,
	Run: func(cmd *cobra.Command, args []string) {
		client, err := reckoner.NewClient(courseFile, version, runAll, onlyRun, true, dryRun)
		if err != nil {
			klog.Fatal(err)
		}
		output, err := client.Plot()
		if err != nil {
			klog.Fatal(err)
		}
		fmt.Println(output)
	},
}

var templateCmd = &cobra.Command{
	Use:     "template",
	Short:   "template <course file>",
	Long:    "Templates a helm chart for a release or several releases.",
	PreRunE: validateArgs,
	Run: func(cmd *cobra.Command, args []string) {
		client, err := reckoner.NewClient(courseFile, version, runAll, onlyRun, false, dryRun)
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
	Use:     "diff",
	Short:   "diff <course file>",
	Long:    "Diffs the currently defined release and the one in the cluster",
	PreRunE: validateArgs,
	Run: func(cmd *cobra.Command, args []string) {
		// TODO: Call Diff
	},
}

var lintCmd = &cobra.Command{
	Use:     "lint",
	Short:   "lint <course file>",
	Long:    "Lints the course file. Checks for structure and valid yaml.",
	PreRunE: validateArgs,
	Run: func(cmd *cobra.Command, args []string) {
		// TODO: Call Lint
	},
}

var convertCmd = &cobra.Command{
	Use:     "convert",
	Short:   "convert <course file> from v1 to v2 schema",
	Long:    "Converts a course file from the v1 python schema to v2 go schema",
	PreRunE: validateArgs,
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

// validateArgs ensures that the only argument passed is a course
// file that exists
func validateArgs(cmd *cobra.Command, args []string) (err error) {
	courseFile, err = reckoner.ValidateArgs(runAll, onlyRun, args)

	return err
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
