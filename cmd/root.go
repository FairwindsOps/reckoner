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
	"k8s.io/klog/v2"

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
	// continueOnError contains the boolean flag to continue processing releases even if one errors
	continueOnError bool
	// inPlaceConvert contains the boolean flag to update the course file in place
	inPlaceConvert bool
	// noColor contains the boolean flag to disable color output
	noColor bool
	// importNamespace is the namespace that contains the release to be imported
	importNamespace string
	// importRelease is the name of the release to be imported
	importRelease string
	// importRepository is the helm repository for the imported release
	importRepository string
	// additionalHelmArgs is a list of arguments to add to all helm commands
	additionalHelmArgs []string
)

func init() {
	rootCmd.PersistentFlags().BoolVarP(&runAll, "run-all", "a", false, "Install every release in the course file")
	rootCmd.PersistentFlags().StringSliceVarP(&onlyRun, "only", "o", nil, "Only install this list of releases. Can be passed multiple times.")
	rootCmd.PersistentFlags().BoolVar(&dryRun, "dry-run", false, "Implies helm --dry-run --debug and skips any hooks")
	rootCmd.PersistentFlags().BoolVar(&createNamespaces, "create-namespaces", true, "If true, allow reckoner to create namespaces.")
	rootCmd.PersistentFlags().BoolVar(&noColor, "no-color", false, "If true, don't colorize output.")
	rootCmd.PersistentFlags().StringSliceVar(&additionalHelmArgs, "helm-args", nil, "Additional arguments to pass to helm commands. Can be passed multiple times. used more than once. WARNING: Setting this will completely override any helm_args in the course.")

	plotCmd.PersistentFlags().BoolVar(&continueOnError, "continue-on-error", false, "If true, continue plotting releases even if one or more has errors.")
	updateCmd.PersistentFlags().BoolVar(&continueOnError, "continue-on-error", false, "If true, continue plotting releases even if one or more has errors.")
	diffCmd.PersistentFlags().BoolVar(&continueOnError, "continue-on-error", false, "If true, continue plotting releases even if one or more has errors.")

	convertCmd.Flags().BoolVarP(&inPlaceConvert, "in-place", "i", false, "If specified, will update the file in place, otherwise outputs to stdout.")

	importCmd.Flags().StringVar(&importNamespace, "namespace", "", "Namespace that contains the release to be imported.")
	importCmd.Flags().StringVar(&importRelease, "release_name", "", "The name of the release to import.")
	importCmd.Flags().StringVar(&importRepository, "repository", "", "The helm repository for the imported release.")

	rootCmd.AddCommand(
		plotCmd,
		convertCmd,
		templateCmd,
		diffCmd,
		lintCmd,
		getManifestsCmd,
		updateCmd,
		importCmd,
		updateReckonerCmd,
	)

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
	PreRunE: validateCobraArgs,
	Run: func(cmd *cobra.Command, args []string) {
		client := reckoner.Client{
			ReckonerVersion:  version,
			Schema:           courseSchema,
			HelmArgs:         additionalHelmArgs,
			DryRun:           dryRun,
			CreateNamespaces: createNamespaces,
			ContinueOnError:  continueOnError,
			Releases:         onlyRun,
		}
		err := client.Init(courseFile, true)
		if err != nil {
			color.Red(err.Error())
			os.Exit(1)
		}
		err = client.Plot()
		if err != nil {
			color.Red(err.Error())
			os.Exit(1)
		}
		if client.Errors > 0 {
			os.Exit(1)
		}
	},
}

var templateCmd = &cobra.Command{
	Use:     "template",
	Short:   "template <course file>",
	Long:    "Templates a helm chart for a release or several releases. Automatically sets --create-namespaces=false --dry-run=true",
	PreRunE: validateCobraArgs,
	Run: func(cmd *cobra.Command, args []string) {
		client := reckoner.Client{
			ReckonerVersion:  version,
			Schema:           courseSchema,
			HelmArgs:         additionalHelmArgs,
			DryRun:           true,
			CreateNamespaces: false,
			ContinueOnError:  continueOnError,
			Releases:         onlyRun,
		}

		err := client.Init(courseFile, false)
		if err != nil {
			color.Red(err.Error())
			os.Exit(1)
		}
		tmpl, err := client.TemplateAll()
		if err != nil {
			color.Red(err.Error())
			os.Exit(1)
		}
		fmt.Println(tmpl)
	},
}

var getManifestsCmd = &cobra.Command{
	Use:     "get-manifests",
	Short:   "get-manifests <course file>",
	Long:    "Gets the manifests currently in the cluster.",
	PreRunE: validateCobraArgs,
	Run: func(cmd *cobra.Command, args []string) {
		client := reckoner.Client{
			ReckonerVersion:  version,
			Schema:           courseSchema,
			HelmArgs:         additionalHelmArgs,
			DryRun:           true,
			CreateNamespaces: false,
			ContinueOnError:  false,
			Releases:         onlyRun,
		}
		err := client.Init(courseFile, true)
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
	PreRunE: validateCobraArgs,
	Run: func(cmd *cobra.Command, args []string) {
		client := reckoner.Client{
			ReckonerVersion:  version,
			Schema:           courseSchema,
			HelmArgs:         additionalHelmArgs,
			DryRun:           true,
			CreateNamespaces: false,
			ContinueOnError:  continueOnError,
			Releases:         onlyRun,
		}
		err := client.Init(courseFile, true)
		if err != nil {
			color.Red(err.Error())
			os.Exit(1)
		}

		if err := client.UpdateHelmRepos(); err != nil {
			color.Red(err.Error())
			os.Exit(1)
		}
		err = client.Diff()
		if err != nil {
			color.Red(err.Error())
			os.Exit(1)
		}
		if client.Errors > 0 {
			os.Exit(1)
		}
	},
}

var lintCmd = &cobra.Command{
	Use:   "lint",
	Short: "lint <course file>",
	Long:  "Lints the course file. Checks for structure and valid yaml.",
	PreRunE: func(cmd *cobra.Command, args []string) error {
		runAll = true
		return validateCobraArgs(cmd, args)
	},
	Run: func(cmd *cobra.Command, args []string) {
		client := reckoner.Client{
			ReckonerVersion:  version,
			Schema:           courseSchema,
			HelmArgs:         additionalHelmArgs,
			DryRun:           true,
			CreateNamespaces: false,
			ContinueOnError:  false,
			Releases:         onlyRun,
		}
		err := client.Init(courseFile, false)
		if err != nil {
			color.Red(err.Error())
			os.Exit(1)
		}

		color.Green("No schema validation errors found in course file: %s", courseFile)
	},
}

var convertCmd = &cobra.Command{
	Use:   "convert",
	Short: "convert <course file>",
	Long:  "Converts a course file from the v1 python schema to v2 go schema",
	PreRunE: func(cmd *cobra.Command, args []string) error {
		runAll = true
		return validateCobraArgs(cmd, args)
	},
	Run: func(cmd *cobra.Command, args []string) {
		newCourse, err := course.OpenCourseFile(courseFile, courseSchema)
		if err != nil {
			color.Red(err.Error())
			os.Exit(1)
		}
		w := os.Stdout
		if inPlaceConvert {
			f, err := os.OpenFile(courseFile, os.O_RDWR, 0644)
			if err != nil {
				color.Red(err.Error())
				os.Exit(1)
			}
			defer f.Close()
			err = f.Truncate(0)
			if err != nil {
				color.Red("failed to truncate course file \"%s\": %s", courseFile, err)
				os.Exit(1)
			}
			w = f
		}
		e := yaml.NewEncoder(w)
		defer e.Close()
		// We prefer 2 spaces in yaml
		e.SetIndent(2)

		err = e.Encode(newCourse)
		if err != nil {
			color.Red(err.Error())
			os.Exit(1)
		}
	},
}

var updateCmd = &cobra.Command{
	Use:     "update",
	Short:   "update <course file>",
	Long:    "Only install/upgrade a release if there are changes.",
	PreRunE: validateCobraArgs,
	Run: func(cmd *cobra.Command, args []string) {
		client := reckoner.Client{
			ReckonerVersion:  version,
			Schema:           courseSchema,
			HelmArgs:         additionalHelmArgs,
			DryRun:           dryRun,
			CreateNamespaces: createNamespaces,
			ContinueOnError:  continueOnError,
			Releases:         onlyRun,
		}
		err := client.Init(courseFile, true)
		if err != nil {
			color.Red(err.Error())
			os.Exit(1)
		}
		err = client.Update()
		if err != nil {
			color.Red(err.Error())
			os.Exit(1)
		}
		if client.Errors > 0 {
			os.Exit(1)
		}
	},
}

var importCmd = &cobra.Command{
	Use:   "import",
	Short: "import",
	Long:  "Outputs a release block that can be used to import the specified release.",
	PreRunE: func(cmd *cobra.Command, args []string) error {
		if importNamespace == "" || importRelease == "" || importRepository == "" {
			return fmt.Errorf("import requires --namespace, --release, and --repository")
		}
		return nil
	},
	Run: func(cmd *cobra.Command, args []string) {
		color.Yellow("Import is experimental and may be unreliable. Double check all output. Output assumes course schema v2.")
		out, err := reckoner.ImportOutput(importRelease, importNamespace, importRepository)
		if err != nil {
			color.Red(err.Error())
			os.Exit(1)
		}
		fmt.Println(out)
	},
}

// getCourseFilePath returns the path to a course YAML file. This does not guarantee the file exists.
// The order of precedence is as follows (higher overrides lower)
// - command-line argument
// - environment variable
// - default value (nothing above was specified)
func getCourseFilePath(args []string) string {
	// attempt to get the course file from environment variable
	courseFile = os.Getenv("RECKONER_COURSE_FILE") // environment variable override

	// if the environment variable was unset or zero-length,
	// try default value of 'course.yml'
	if len(courseFile) == 0 {
		courseFile = "course.yml" // default course file
	}

	// allow cli argument to override everything else
	if len(args) > 0 { // an argument was passed
		courseFile = args[0] // use it
	}

	return courseFile
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
