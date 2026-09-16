#!/bin/bash
set -e

make build
docker exec e2e-command-runner mkdir -p /tmp/test-results
docker cp . e2e-command-runner:/reckoner
