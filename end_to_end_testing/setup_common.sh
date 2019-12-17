#!/bin/bash

set -e
set -o pipefail


echo "Installing git and jq"
sudo apt-get update
sudo apt-get install -yqq jq git

echo "Installing Reckoner"
sudo cp /tmp/binaries/reckoner-linux-amd64 /usr/local/bin/reckoner
reckoner version

echo "Installing Kind"
curl -sLO https://github.com/kubernetes-sigs/kind/releases/download/v0.4.0/kind-linux-amd64
chmod 0755 kind-linux-amd64
sudo mv kind-linux-amd64 /usr/local/bin/kind
kind version

echo "Installing Kubectl"
curl -sLO https://storage.googleapis.com/kubernetes-release/release/v1.14.4/bin/linux/amd64/kubectl
chmod 0755 kubectl
sudo mv kubectl /usr/local/bin/
kubectl version --client

echo "Creating Kubernetes Cluster with Kind"
kind create cluster --wait=90s --image kindest/node:v1.14.3
docker ps -a

echo "Setting up kubecfg"
cp "$(kind get kubeconfig-path --name=kind)" ~/.kube/config
kubectl version
