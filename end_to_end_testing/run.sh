#!/bin/bash

set -x
chmod +x /usr/local/bin/reckoner
reckoner version

## Install python 3.8 and pip
#apt update
#apt-get -y -o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold' install apt-get install libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev
#wget https://www.python.org/ftp/python/3.8.5/Python-3.8.5.tgz
#tar xzf Python-3.8.5.tgz
#cd Python-3.8.5
#./configure --enable-optimizations
#make altinstall
#curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
#python3.8 get-pip.py
## Install reckone rwith python3.8
#pip3.8 install /reckoner

curl -LO https://github.com/ovh/venom/releases/download/v0.27.0/venom.linux-amd64
mv venom.linux-amd64 /usr/local/bin/venom
chmod +x /usr/local/bin/venom

mkdir -p /tmp/test-results

cd /reckoner/end_to_end_testing
venom run tests/* --log debug --output-dir=/tmp/test-results --strict
exit $?
