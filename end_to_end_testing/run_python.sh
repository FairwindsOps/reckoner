#!/bin/bash

set -x
set -e

python --version

apt-get update
apt-get install python3-pip

cd /reckoner
pip3 install .
reckoner --version

curl -LO https://github.com/ovh/venom/releases/download/v0.27.0/venom.linux-amd64
mv venom.linux-amd64 /usr/local/bin/venom
chmod +x /usr/local/bin/venom

mkdir -p /tmp/test-results

cd /reckoner/end_to_end_testing

# The parallelization number must remain relatively low otherwise the tests become flaky due to resources and pending pods and such
venom run tests/* --log debug --output-dir=/tmp/test-results --parallel=2 --strict
exit $?
