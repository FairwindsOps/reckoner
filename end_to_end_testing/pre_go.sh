#!/bin/bash

docker cp . e2e-command-runner:/reckoner
docker cp /dist e2e-command-runner:/reckoner
