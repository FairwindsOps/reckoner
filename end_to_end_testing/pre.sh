#!/bin/bash

docker cp . e2e-command-runner:/reckoner
docker cp /tmp/binaries/reckoner-linux-amd64 e2e-command-runner:/usr/local/bin/reckoner
