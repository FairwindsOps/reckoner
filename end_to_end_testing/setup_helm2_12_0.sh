source "$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"/setup_common.sh

echo "Installing Helm 2.12.0"
curl -sL https://storage.googleapis.com/kubernetes-helm/helm-v2.12.0-linux-amd64.tar.gz | tar xzv linux-amd64/helm
sudo mv linux-amd64/helm /usr/local/bin/helm
rm -rf linux-amd64
helm version --client

echo "Setting up Helm on Kubernetes"
kubectl -n kube-system create serviceaccount tiller
kubectl create clusterrolebinding tiller --clusterrole cluster-admin --serviceaccount kube-system:tiller
helm init --service-account tiller --wait
