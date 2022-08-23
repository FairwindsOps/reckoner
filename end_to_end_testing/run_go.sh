#!/bin/bash

set -x
set -e

# Install Go
curl -LO https://go.dev/dl/go1.18.5.linux-amd64.tar.gz

tar -C /usr/local -xzf go1.18.5.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
go version

# build
cd /reckoner
make build

mv /reckoner/reckoner-go /usr/local/bin/reckoner
reckoner version

curl -LO https://github.com/ovh/venom/releases/download/v0.28.0/venom.linux-amd64
mv venom.linux-amd64 /usr/local/bin/venom
chmod +x /usr/local/bin/venom

mkdir -p /tmp/test-results

cd /reckoner/end_to_end_testing

# The parallelization number must remain relatively low otherwise the tests become flaky due to resources and pending pods and such
venom run tests/* --log debug --output-dir=/tmp/test-results --parallel=2 --strict
exit $?
