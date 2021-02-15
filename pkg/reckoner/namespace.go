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

	v1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
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

// PatchNamespace updates a kubernetes namespace with the given annotations and labels
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
