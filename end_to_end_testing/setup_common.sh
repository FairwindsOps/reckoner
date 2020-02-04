#!/bin/bash

set -e
set -o pipefail

sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 78BD65473CB3BD13
wget -qO - https://packagecloud.io/circleci/trusty/gpgkey | sudo apt-key add -

echo "Installing git and jq"
sudo apt-get update
sudo apt-get install -yqq jq git

echo "Installing Reckoner"
sudo cp /tmp/binaries/reckoner-linux-amd64 /usr/local/bin/reckoner
reckoner version

echo "Installing Kind"
curl -sLO https://github.com/kubernetes-sigs/kind/releases/download/v0.7.0/kind-linux-amd64
chmod 0755 kind-linux-amd64
sudo mv kind-linux-amd64 /usr/local/bin/kind
kind version

echo "Installing Kubectl"
curl -sLO https://storage.googleapis.com/kubernetes-release/release/v1.15.7/bin/linux/amd64/kubectl
chmod 0755 kubectl
sudo mv kubectl /usr/local/bin/
kubectl version --client

echo "Creating Kubernetes Cluster with Kind"
kind create cluster --wait=90s --image kindest/node:v1.15.7@sha256:e2df133f80ef633c53c0200114fce2ed5e1f6947477dbc83261a6a921169488d
docker ps -a

kubectl version
