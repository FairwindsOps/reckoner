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

	fakeClient.CreateNamespace(name, annotations, labels)

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

	fakeClient.CreateNamespace(name, annotations, labels)

	newAnnotations := map[string]string{"service.beta.kubernetes.io/aws-load-balancer-internal": "0.0.0.0/0"}

	newLabels := map[string]string{"istio-injection": "enabled"}

	fakeClient.PatchNamespace(name, newAnnotations, newLabels)

	updatedNamespace, err := fakeKubeClinet.CoreV1().Namespaces().Get(context.TODO(), name, metav1.GetOptions{})

	updatedAnnotations := map[string]string{"nginx.ingress.kubernetes.io/http2-push-preload": "true", "service.beta.kubernetes.io/aws-load-balancer-internal": "0.0.0.0/0"}

	updatedLabels := map[string]string{"app.kubernetes.io/name": "ingress-nginx", "istio-injection": "enabled"}

	assert.NoError(t, err)

	assert.Equal(t, name, updatedNamespace.Name)

	assert.NoError(t, err)

	assert.Equal(t, updatedLabels, updatedNamespace.Labels)

	assert.Equal(t, updatedAnnotations, updatedNamespace.Annotations)

}
