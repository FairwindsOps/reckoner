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
	"context"
	"encoding/json"

	"github.com/fairwindsops/reckoner/pkg/course"
	"github.com/thoas/go-funk"
	v1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/klog"
)

// CreateNamespace creates a kubernetes namespace with the given annotations and labels
func (c *Client) CreateNamespace(namespace string, annotations, labels map[string]string) error {
	ns := &v1.Namespace{
		ObjectMeta: metav1.ObjectMeta{
			Name:        namespace,
			Annotations: annotations,
			Labels:      labels,
		},
	}
	_, err := c.KubeClient.CoreV1().Namespaces().Create(context.TODO(), ns, metav1.CreateOptions{})
	if err != nil {
		return err
	}
	return nil
}

// PatchNamespace patches a kubernetes namespace with the given annotations and labels
func (c *Client) PatchNamespace(namespace string, annotations, labels map[string]string) error {
	ns := &v1.Namespace{
		ObjectMeta: metav1.ObjectMeta{
			Annotations: annotations,
			Labels:      labels,
		},
	}
	data, err := json.Marshal(ns)
	if err != nil {
		return err
	}
	_, err = c.KubeClient.CoreV1().Namespaces().Patch(context.TODO(), namespace, types.StrategicMergePatchType, data, metav1.PatchOptions{})
	if err != nil {
		return err
	}

	return nil
}

// NamespaceManagement manages namespace names, annotations and labels
func (c *Client) NamespaceManagement() error {
	if c.DryRun {
		klog.Warningf("namespace management not run due to --dry-run: %v", c.DryRun)
		return nil
	}

	namespaces, err := c.KubeClient.CoreV1().Namespaces().List(context.TODO(), metav1.ListOptions{})
	if err != nil {
		return err
	}
	if c.CourseFile.DefaultNamespace != "" {
		err := c.CreateOrPatchNamespace(c.CourseFile.NamespaceMgmt.Default.Settings.Overwrite, c.CourseFile.DefaultNamespace, c.CourseFile.NamespaceMgmt.Default, namespaces)
		if err != nil {
			return err
		}
	}
	for _, release := range c.CourseFile.Releases {
		err := c.CreateOrPatchNamespace(release.NamespaceMgmt.Settings.Overwrite, release.Namespace, release.NamespaceMgmt, namespaces)
		if err != nil {
			return err
		}

	}
	return nil
}

// CreateOrPatchNamespace creates or patches namespace based on the configurations
func (c *Client) CreateOrPatchNamespace(overWrite bool, namespaceName string, namespaceMgmt course.NamespaceConfig, namespaces *v1.NamespaceList) error {
	ns := checkIfNamespaceExists(namespaces, namespaceName)
	var err error
	if ns != nil {
		annotations, labels := labelsAndAnnotationsToUpdate(overWrite, namespaceMgmt.Metadata.Annotations, namespaceMgmt.Metadata.Labels, ns)
		err = c.PatchNamespace(namespaceName, annotations, labels)
	} else {
		err = c.CreateNamespace(namespaceName, namespaceMgmt.Metadata.Annotations, namespaceMgmt.Metadata.Labels)
	}
	return err
}

func checkIfNamespaceExists(nsList *v1.NamespaceList, nsName string) *v1.Namespace {
	nsInterface := funk.Find(nsList.Items, func(ns v1.Namespace) bool {
		return ns.Name == nsName
	})
	if nsInterface != nil {
		namespace := nsInterface.(v1.Namespace)
		return &namespace
	}
	return nil
}

func labelsAndAnnotationsToUpdate(overwrite bool, annotations, labels map[string]string, ns *v1.Namespace) (finalAnnotations, finalLabels map[string]string) {
	if overwrite {
		return annotations, labels
	}
	finalLabels = filterMapString(labels, ns.Labels)
	finalAnnotations = filterMapString(annotations, ns.Annotations)
	return finalAnnotations, finalLabels
}

func filterMapString(newLabelsOrAnnotations, nsLabelOrAnnotations map[string]string) map[string]string {
	finalLabelsOrAnnotations := map[string]string{}
	keys := funk.Keys(newLabelsOrAnnotations).([]string)
	for _, key := range keys {
		if !funk.Contains(nsLabelOrAnnotations, key) {
			finalLabelsOrAnnotations[key] = newLabelsOrAnnotations[key]
		}
	}
	return finalLabelsOrAnnotations
}
