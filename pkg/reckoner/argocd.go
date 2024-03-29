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
	"bytes"
	"errors"
	"os"
	"strings"

	"github.com/fairwindsops/reckoner/pkg/course"
	"github.com/fatih/color"
	"github.com/imdario/mergo"
	"gopkg.in/yaml.v3"
	"k8s.io/klog/v2"
)

func generateArgoApplication(release course.Release, courseFile course.FileV2) (app course.ArgoApplication, err error) {
	app = courseFile.GitOps.ArgoCD // use global config at root of course file

	// if release.GitOps.ArgoCD.<whatever> exists, override the app.<whatever> with that one, recursively.
	err = mergo.Merge(&app, release.GitOps.ArgoCD, mergo.WithOverride)
	if err != nil {
		return app, err
	}

	// default to a kind of Application if it was omitted in the course file
	if app.Kind == "" {
		app.Kind = "Application"
	}

	// default to an API version of v1alpha1 if it was omitted in the course file
	if app.APIVersion == "" {
		app.APIVersion = "argoproj.io/v1alpha1"
	}

	// unless they overrode it in the course file, assume the name of the argocd app is the same as the helm release
	// app:release should be a 1:1
	if app.Metadata.Name == "" {
		app.Metadata.Name = release.Name
	}

	// Application.Metadata.Namespace is where the ArgoCD Application resource will go (not the helm release)
	if app.Metadata.Namespace == "" {
		klog.V(3).Infoln("No namespace declared in course file. Your ArgoCD Application manifests will likely get applied to the agent's default context.")
	}

	// default source path to release name
	if app.Spec.Source.Path == "" {
		klog.V(3).Infoln("No .gitops.argocd.spec.source.path declared in course file for " + release.Name + ". The path has been set to its name.")
		app.Spec.Source.Path = release.Name
	}

	// don't support ArgoCD Application spec.destination.namespace at all
	if app.Spec.Destination.Namespace != "" {
		klog.V(3).Infoln("Refusing to respect the .gitops.argocd.spec.destination.namespace value declared in course file for " + release.Name + ". Using the release namespace instead, if it exists. If none is specified, the default at the root of the course YAML file will be used. Remove the namespace from the ArgoCD destination to stop seeing this warning.")
	}

	// Application.Spec.Destination.Namespace is where the helm releases will be applied
	if release.Namespace != "" { // there's a specific namespace for this release
		app.Spec.Destination.Namespace = release.Namespace // specify it as the destination namespace
	} else { // nothing was specified in the release
		app.Spec.Destination.Namespace = courseFile.DefaultNamespace // use the default namespace at the root of the course file
	}

	if app.Spec.Destination.Server == "" {
		klog.V(3).Infoln("No .gitops.argocd.spec.destination.server declared in course file for " + release.Name + ". Assuming you want the kubernetes service in the default namespace. Specify to make this warning go away.")
		app.Spec.Destination.Server = "https://kubernetes.default.svc"
	}

	if app.Spec.Project == "" {
		klog.V(3).Infoln("No .gitops.argocd.spec.project declared in course file for " + release.Name + ". We'll set it to a sensible default value of 'default'. Specify to make this warning go away.")
		app.Spec.Project = "default"
	}

	return app, err
}

func (c *Client) WriteArgoApplications(outputDir string) (err error) {
	appsOutputDir := outputDir + "/argocd-apps"
	for _, dir := range []string{outputDir, appsOutputDir} {
		if _, err := os.Stat(dir); errors.Is(err, os.ErrNotExist) {
			err := os.Mkdir(dir, os.ModePerm)
			if err != nil {
				return err
			}
		}
	}

	for _, release := range c.CourseFile.Releases {
		// generate an argocd application resource
		app, err := generateArgoApplication(*release, c.CourseFile)
		if err != nil {
			return err
		}

		if app.Metadata.Name == "" {
			color.Yellow("No metadata found for release " + release.Name + ". Skipping ArgoCD Applicationgeneration...")
			continue
		}

		// generate name of app file
		appOutputFile := appsOutputDir + "/" + strings.ToLower(app.Metadata.Name) + ".yaml"

		// prepare to write stuff (pretty)
		var b bytes.Buffer                 // used for encoding & return
		yamlEncoder := yaml.NewEncoder(&b) // create an encoder to handle custom configuration
		yamlEncoder.SetIndent(2)           // people expect two-space indents instead of the default four
		err = yamlEncoder.Encode(&app)     // encode proper YAML into slice of bytes
		if err != nil {                    // check for errors
			return err // bubble up
		}

		// write stuff
		err = writeYAML(b.Bytes(), appOutputFile)
		if err != nil { // check for errors
			return err // bubble up
		}
	}

	return err
}
