package reckoner

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
	v1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes/fake"
)

func TestCreateNamespace(t *testing.T) {
	fakeKubeClinet := fake.NewSimpleClientset(&v1.Namespace{})
	fakeClient := Client{
		KubeClient: fakeKubeClinet,
	}

	name := "reckoner"
	annotations := map[string]string{"nginx.ingress.kubernetes.io/http2-push-preload": "true"}
	labels := map[string]string{"app.kubernetes.io/name": "ingress-nginx"}
	err := fakeClient.CreateNamespace(name, annotations, labels)
	assert.NoError(t, err)

	namespace, err := fakeKubeClinet.CoreV1().Namespaces().Get(context.TODO(), name, metav1.GetOptions{})
	assert.NoError(t, err)
	assert.Equal(t, name, namespace.Name)
	assert.NoError(t, err)
	assert.Equal(t, labels, namespace.Labels)
	assert.Equal(t, annotations, namespace.Annotations)

}

func TestPatchNamespace(t *testing.T) {
	fakeKubeClinet := fake.NewSimpleClientset(&v1.Namespace{})
	fakeClient := Client{
		KubeClient: fakeKubeClinet,
	}

	name := "reckoner"
	annotations := map[string]string{"nginx.ingress.kubernetes.io/http2-push-preload": "true"}
	labels := map[string]string{"app.kubernetes.io/name": "ingress-nginx"}
	err := fakeClient.CreateNamespace(name, annotations, labels)
	assert.NoError(t, err)

	newAnnotations := map[string]string{"service.beta.kubernetes.io/aws-load-balancer-internal": "0.0.0.0/0"}
	newLabels := map[string]string{"istio-injection": "enabled"}
	err = fakeClient.PatchNamespace(name, newAnnotations, newLabels)
	assert.NoError(t, err)

	updatedAnnotations := map[string]string{"nginx.ingress.kubernetes.io/http2-push-preload": "true", "service.beta.kubernetes.io/aws-load-balancer-internal": "0.0.0.0/0"}
	updatedLabels := map[string]string{"app.kubernetes.io/name": "ingress-nginx", "istio-injection": "enabled"}
	updatedNamespace, err := fakeKubeClinet.CoreV1().Namespaces().Get(context.TODO(), name, metav1.GetOptions{})
	assert.NoError(t, err)
	assert.Equal(t, name, updatedNamespace.Name)
	assert.Equal(t, updatedLabels, updatedNamespace.Labels)
	assert.Equal(t, updatedAnnotations, updatedNamespace.Annotations)

}

func TestCheckIfNamespaceExist(t *testing.T) {
	fakeKubeClinet := fake.NewSimpleClientset(&v1.Namespace{})
	fakeClient := Client{
		KubeClient: fakeKubeClinet,
	}

	name := "reckoner"
	annotations := map[string]string{"nginx.ingress.kubernetes.io/http2-push-preload": "true"}
	labels := map[string]string{"app.kubernetes.io/name": "ingress-nginx"}
	err := fakeClient.CreateNamespace(name, annotations, labels)
	assert.NoError(t, err)

	nsList, err := fakeClient.KubeClient.CoreV1().Namespaces().List(context.TODO(), metav1.ListOptions{})
	assert.NoError(t, err)

	ns := checkIfNamespaceExists(nsList, name)
	assert.NotNil(t, ns)
	assert.Equal(t, name, ns.Name)

	ns = checkIfNamespaceExists(nsList, "emptyns")
	assert.Nil(t, ns)
}

func TestLabelsAndAnnotationsToUpdate(t *testing.T) {
	fakeKubeClinet := fake.NewSimpleClientset(&v1.Namespace{})
	fakeClient := Client{
		KubeClient: fakeKubeClinet,
	}

	name := "reckoner"
	annotations := map[string]string{"nginx.ingress.kubernetes.io/http2-push-preload": "true"}
	labels := map[string]string{"app.kubernetes.io/name": "ingress-nginx"}
	err := fakeClient.CreateNamespace(name, annotations, labels)
	assert.NoError(t, err)

	newLabels := map[string]string{"app.kubernetes.io/name": "ingress-nginx-new", "label-key-1": "label-value-1"}
	newAnnotations := map[string]string{"nginx.ingress.kubernetes.io/http2-push-preload": "false"}
	ns, err := fakeClient.KubeClient.CoreV1().Namespaces().Get(context.TODO(), name, metav1.GetOptions{})
	assert.NoError(t, err)

	updatedAnnotations, updatedLabels := labelsAndAnnotationsToUpdate(true, newAnnotations, newLabels, ns)
	assert.Equal(t, newAnnotations, updatedAnnotations)
	assert.Equal(t, newLabels, updatedLabels)

	expectedLabels := map[string]string{"label-key-1": "label-value-1"}
	expectedAnnotations := map[string]string{}
	updatedAnnotations, updatedLabels = labelsAndAnnotationsToUpdate(false, newAnnotations, newLabels, ns)
	assert.Equal(t, expectedLabels, updatedLabels)
	assert.Equal(t, expectedAnnotations, updatedAnnotations)
}
