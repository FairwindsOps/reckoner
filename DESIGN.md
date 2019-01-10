# Reckoner 

## Intent
Reckoner is intended to provide a declarative syntax to install and manage multiple Helm releases. A primary additional feature is the ability to pull from a git repository instead of a local chart or chart repository.

## Key Design Features

* A stable declarative syntax for Helm releases and their configuration values
* The ability to pull a chart from a git repository
* Pre and Post hooks to provide extra steps not included in the Helm chart installation

## Scope

### In Scope:
* Interaction with the Helm Client
* Translation of configuration to a helm command
* Staying up to date with Helm features and commands


### Out of Scope:
* Direct interaction with the Tiller api
* Replacing Tiller
* Creation or modification of Helm charts
* Overwriting portions of a chart's output (eg Kustomize or Ship)
* Managing installation versions of Helm and Tiller


## Architecture

TBD
