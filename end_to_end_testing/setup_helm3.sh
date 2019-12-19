source "$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"/setup_common.sh

echo "Installing Helm"
curl -sL https://get.helm.sh/helm-v3.0.2-linux-amd64.tar.gz | tar xzv linux-amd64/helm
sudo mv linux-amd64/helm /usr/local/bin/helm
rm -rf linux-amd64
helm version

helm repo add stable https://kubernetes-charts.storage.googleapis.com
