#!/bin/bash

set -x
set -e

python --version

cd /reckoner
pip install --user reckoner
reckoner --version

curl -LO https://github.com/ovh/venom/releases/download/v0.27.0/venom.linux-amd64
mv venom.linux-amd64 /usr/local/bin/venom
chmod +x /usr/local/bin/venom

mkdir -p /tmp/test-results

cd /reckoner/end_to_end_testing
venom run tests/* --log debug --output-dir=/tmp/test-results --strict
exit $?
