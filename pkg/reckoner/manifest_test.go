package reckoner

import "testing"

var testManifestsString = `
---
# Source: example/templates/controller-serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: example-controller
  labels:
    app.kubernetes.io/name: example
    helm.sh/chart: example-1.0.0
    app.kubernetes.io/instance: example
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/component: controller
---
# Source: example/templates/controller-clusterrole.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: example-controller
  labels:
    app.kubernetes.io/name: example
    helm.sh/chart: example-1.0.0
    app.kubernetes.io/instance: example
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/component: controller
rules:
  - apiGroups:
      - 'apps'
    resources:
      - '*'
    verbs:
      - 'get'
      - 'list'
      - 'watch'
  - apiGroups:
      - ''
    resources:
      - 'namespaces'
      - 'pods'
    verbs:
      - 'get'
      - 'list'
      - 'watch'
  - apiGroups:
      - 'autoscaling.k8s.io'
    resources:
      - 'verticalpodautoscalers'
    verbs:
      - 'get'
      - 'list'
      - 'create'
      - 'delete'
      - 'update'
`

func TestManifestUnmarshal(t *testing.T) {
	manifests, err := ManifestUnmarshal(testManifestsString)
	if err != nil {
		t.Fatal(err)
	}
	if len(manifests) != 2 {
		t.Fatalf("Expected 2 manifests, got %d", len(manifests))
	}

	// Test first manifest
	if manifests[0].Kind != "ServiceAccount" {
		t.Errorf("Expected first manifest's Kind to be ServiceAccount, got %s", manifests[0].Kind)
	}
	if manifests[0].Metadata.Name != "example-controller" {
		t.Errorf("Expected first manifest's Metadata.Name to be example-controller, got %s", manifests[0].Metadata.Name)
	}
	if manifests[0].Source != "example/templates/controller-serviceaccount.yaml" {
		t.Errorf("Expected first manifest's Source to be example/templates/controller-serviceaccount.yaml, got %s", manifests[0].Source)
	}

	// Test second manifest
	if manifests[1].Kind != "ClusterRole" {
		t.Errorf("Expected second manifest's Kind to be ClusterRole, got %s", manifests[1].Kind)
	}
	if manifests[1].Metadata.Name != "example-controller" {
		t.Errorf("Expected second manifest's Metadata.Name to be example-controller, got %s", manifests[1].Metadata.Name)
	}
	if manifests[1].Source != "example/templates/controller-clusterrole.yaml" {
		t.Errorf("Expected second manifest's Source to be example/templates/controller-clusterrole.yaml, got %s", manifests[1].Source)
	}
}
