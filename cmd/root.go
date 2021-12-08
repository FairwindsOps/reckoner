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

	"github.com/fatih/color"
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
	courseSchema  []byte

	// runAll contains the boolean flag to install all the releases
	runAll bool
	// dryRun contains the boolean flag to run as dry run
	dryRun bool
	// courseFile is the name and path of the course.yml file
	courseFile string
	// onlyRun contains the list of releases to install
	onlyRun []string
	// createNamespaces contains the boolean flag to create namespaces
	createNamespaces bool
	// inPlaceConvert contains the boolean flag to update the course file in place
	inPlaceConvert bool
	// noColor contains the boolean flag to disable color output
	noColor bool
)

func init() {
	rootCmd.PersistentFlags().BoolVarP(&runAll, "run-all", "a", false, "Install every release in the course file")
	rootCmd.PersistentFlags().StringSliceVarP(&onlyRun, "only", "o", nil, "Only install this list of releases. Can be passed multiple times.")
	rootCmd.PersistentFlags().BoolVar(&dryRun, "dry-run", false, "Implies helm --dry-run --debug and skips any hooks")
	rootCmd.PersistentFlags().BoolVar(&createNamespaces, "create-namespaces", true, "If true, allow reckoner to create namespaces.")
	rootCmd.PersistentFlags().BoolVar(&noColor, "no-color", false, "If true, don't colorize output.")

	convertCmd.Flags().BoolVarP(&inPlaceConvert, "in-place", "i", false, "If specified, will update the file in place, otherwise outputs to stdout.")

	// add commands here
	rootCmd.AddCommand(plotCmd)
	rootCmd.AddCommand(convertCmd)
	rootCmd.AddCommand(templateCmd)
	rootCmd.AddCommand(diffCmd)
	rootCmd.AddCommand(lintCmd)
	rootCmd.AddCommand(getManifestsCmd)
	rootCmd.AddCommand(updateCmd)

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
		client, err := reckoner.NewClient(courseFile, version, runAll, onlyRun, true, dryRun, createNamespaces, courseSchema)
		if err != nil {
			klog.Fatal(err)
		}
		err = client.Plot()
		if err != nil {
			klog.Fatal(err)
		}
	},
}

var templateCmd = &cobra.Command{
	Use:     "template",
	Short:   "template <course file>",
	Long:    "Templates a helm chart for a release or several releases. Automatically sets --create-namespaces=false --dry-run=true",
	PreRunE: validateArgs,
	Run: func(cmd *cobra.Command, args []string) {
		client, err := reckoner.NewClient(courseFile, version, runAll, onlyRun, false, true, false, courseSchema)
		if err != nil {
			klog.Fatal(err)
		}
		tmpl, err := client.TemplateAll()
		if err != nil {
			klog.Fatal(err)
		}
		fmt.Println(tmpl)
	},
}

var getManifestsCmd = &cobra.Command{
	Use:     "get-manifests",
	Short:   "get-manifests <course file>",
	Long:    "Gets the manifests currently in the cluster.",
	PreRunE: validateArgs,
	Run: func(cmd *cobra.Command, args []string) {
		client, err := reckoner.NewClient(courseFile, version, runAll, onlyRun, false, true, false, courseSchema)
		if err != nil {
			color.Red(err.Error())
			os.Exit(1)
		}
		manifests, err := client.GetManifests()
		if err != nil {
			color.Red(err.Error())
			os.Exit(1)
		}
		fmt.Print(manifests)
	},
}

var diffCmd = &cobra.Command{
	Use:     "diff",
	Short:   "diff <course file>",
	Long:    "Diffs the currently defined release and the one in the cluster",
	PreRunE: validateArgs,
	Run: func(cmd *cobra.Command, args []string) {
		client, err := reckoner.NewClient(courseFile, version, runAll, onlyRun, false, true, false, courseSchema)
		if err != nil {
			klog.Fatal(err)
		}
		if err := client.UpdateHelmRepos(); err != nil {
			klog.Fatal(err)
		}
		err = client.Diff()
		if err != nil {
			klog.Fatal(err)
		}
	},
}

var lintCmd = &cobra.Command{
	Use:   "lint",
	Short: "lint <course file>",
	Long:  "Lints the course file. Checks for structure and valid yaml.",
	PreRunE: func(cmd *cobra.Command, args []string) error {
		runAll = true
		return validateArgs(cmd, args)
	},
	Run: func(cmd *cobra.Command, args []string) {
		_, err := reckoner.NewClient(courseFile, version, runAll, onlyRun, false, true, false, courseSchema)
		if err != nil {
			klog.Fatal(err)
		}
		klog.Infof("course file %s is good to go!", courseFile)
	},
}

var convertCmd = &cobra.Command{
	Use:   "convert",
	Short: "convert <course file>",
	Long:  "Converts a course file from the v1 python schema to v2 go schema",
	PreRunE: func(cmd *cobra.Command, args []string) error {
		runAll = true
		return validateArgs(cmd, args)
	},
	Run: func(cmd *cobra.Command, args []string) {
		newCourse, err := course.ConvertV1toV2(courseFile)
		if err != nil {
			klog.Fatal(err)
		}
		w := os.Stdout
		if inPlaceConvert {
			f, err := os.OpenFile(courseFile, os.O_RDWR, 0644)
			if err != nil {
				klog.Fatal(err)
			}
			defer f.Close()
			err = f.Truncate(0)
			if err != nil {
				klog.Fatalf("failed to truncate course file \"%s\": %s", courseFile, err)
			}
			w = f
		}
		e := yaml.NewEncoder(w)
		defer e.Close()
		// We prefer 2 spaces in yaml
		e.SetIndent(2)

		err = e.Encode(newCourse)
		if err != nil {
			klog.Fatal(err)
		}
	},
}

var updateCmd = &cobra.Command{
	Use:     "update",
	Short:   "update <course file>",
	Long:    "Only install/upgrade a release if there are changes.",
	PreRunE: validateArgs,
	Run: func(cmd *cobra.Command, args []string) {
		client, err := reckoner.NewClient(courseFile, version, runAll, onlyRun, true, dryRun, createNamespaces, courseSchema)
		if err != nil {
			color.Red(err.Error())
			os.Exit(1)
		}
		err = client.Update()
		if err != nil {
			color.Red(err.Error())
			os.Exit(1)
		}
	},
}

// validateArgs ensures that the only argument passed is a course
// file that exists
func validateArgs(cmd *cobra.Command, args []string) (err error) {
	courseFile, err = reckoner.ValidateArgs(runAll, onlyRun, args)
	color.NoColor = noColor
	klog.V(3).Infof("colorize output: %v", !noColor)

	return err
}

// Execute the stuff
func Execute(VERSION string, COMMIT string, schema []byte) {
	version = VERSION
	versionCommit = COMMIT
	courseSchema = schema
	if err := rootCmd.Execute(); err != nil {
		klog.Error(err)
		os.Exit(1)
	}
}
