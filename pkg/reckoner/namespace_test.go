package reckoner

import (
	"testing"

	"github.com/fairwindsops/reckoner/pkg/course"
	"github.com/fairwindsops/reckoner/pkg/helm"
	v1 "k8s.io/api/core/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/kubernetes/fake"
)

func TestClient_CreateNamespace(t *testing.T) {
	type fields struct {
		KubeClient      kubernetes.Interface
		Helm            helm.Client
		ReckonerVersion string
		CourseFile      course.FileV2
		PlotAll         bool
		Releases        []string
	}
	type args struct {
		namespace   string
		annotations map[string]string
		labels      map[string]string
	}
	tests := []struct {
		name    string
		fields  fields
		args    args
		wantErr bool
	}{
		{
			name:    "empty args",
			args:    args{},
			wantErr: true,
		},
		{
			name: "namespace name provided with no annotations or labels",
			args: args{
				namespace: "example",
			},
			wantErr: false,
		},
		{
			name: "no namespace provided but labels and annotations are passed",
			args: args{
				namespace:   "",
				annotations: map[string]string{"nginx.ingress.kubernetes.io/http2-push-preload": "true"},
				labels:      map[string]string{"app.kubernetes.io/name": "ingress-nginx"},
			},
			wantErr: true,
		},
		{
			name: "namespace provided and labels and annotations are passed",
			args: args{
				namespace:   "nginx",
				annotations: map[string]string{"nginx.ingress.kubernetes.io/http2-push-preload": "true"},
				labels:      map[string]string{"app.kubernetes.io/name": "ingress-nginx"},
			},
			wantErr: false,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			c := &Client{
				KubeClient:      fake.NewSimpleClientset(&v1.Namespace{}),
				Helm:            tt.fields.Helm,
				ReckonerVersion: tt.fields.ReckonerVersion,
				CourseFile:      tt.fields.CourseFile,
				PlotAll:         tt.fields.PlotAll,
				Releases:        tt.fields.Releases,
			}
			if err := c.CreateNamespace(tt.args.namespace, tt.args.annotations, tt.args.labels); (err != nil) != tt.wantErr {
				t.Errorf("Client.CreateNamespace() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

// func TestCreateNamespace(t *testing.T) {

// 	fakeKubeClinet := fake.NewSimpleClientset(&v1.Namespace{})

// 	fakeClient := Client{
// 		KubeClient: fakeKubeClinet,
// 	}

// 	name := "reckoner"

// 	annotations := map[string]string{"nginx.ingress.kubernetes.io/http2-push-preload": "true"}

// 	labels := map[string]string{"app.kubernetes.io/name": "ingress-nginx"}

// 	fakeClient.CreateNamespace(name, annotations, labels)

// 	namespace, err := fakeKubeClient.CoreV1().Namespaces().Get(context.TODO(), name, metav1.GetOptions{})

// 	assert.NoError(t, err)

// 	assert.Equal(t, name, namespace.Name)

// 	assert.NoError(t, err)

// 	assert.Equal(t, labels, namespace.Labels)

// 	assert.Equal(t, annotations, namespace.Annotations)

// }

// func TestPatchNamespace(t *testing.T) {

// 	fakeKubeClinet := fake.NewSimpleClientset(&v1.Namespace{})

// 	fakeClient := Client{
// 		KubeClient: fakeKubeClinet,
// 	}

// 	name := "reckoner"

// 	annotations := map[string]string{"nginx.ingress.kubernetes.io/http2-push-preload": "true"}

// 	labels := map[string]string{"app.kubernetes.io/name": "ingress-nginx"}

// 	fakeClient.CreateNamespace(name, annotations, labels)

// 	newAnnotations := map[string]string{"service.beta.kubernetes.io/aws-load-balancer-internal": "0.0.0.0/0"}

// 	newLabels := map[string]string{"istio-injection": "enabled"}

// 	fakeClient.PatchNamespace(name, newAnnotations, newLabels)

// 	updatedNamespace, err := fakeKubeClinet.CoreV1().Namespaces().Get(context.TODO(), name, metav1.GetOptions{})

// 	updatedAnnotations := map[string]string{"nginx.ingress.kubernetes.io/http2-push-preload": "true", "service.beta.kubernetes.io/aws-load-balancer-internal": "0.0.0.0/0"}

// 	updatedLabels := map[string]string{"app.kubernetes.io/name": "ingress-nginx", "istio-injection": "enabled"}

// 	assert.NoError(t, err)

// 	assert.Equal(t, name, updatedNamespace.Name)

// 	assert.NoError(t, err)

// 	assert.Equal(t, updatedLabels, updatedNamespace.Labels)

// 	assert.Equal(t, updatedAnnotations, updatedNamespace.Annotations)

// }
