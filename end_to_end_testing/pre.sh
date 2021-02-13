#!/bin/bash

make build
docker cp . e2e-command-runner:/reckoner
