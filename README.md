
# autohelm

Command line helper for helm.
This utility adds to the functionality of [Helm](https://github.com/kubernetes/helm) in multiple ways:
* Creates a declarative syntax to manage multiple releases in one place
* Allows installation of charts from a git commit/branch/release

## Requirements
- python >= 2.7
- helm: installed and inited
- $INFRASTRUCTURE_REPO

## Installation
### As standalone shell command
- pip install git+https://github.com/reactiveops/autohelm
### As Helm plugin
- pip install git+https://github.com/reactiveops/autohelm
- helm plugin install https://github.com/reactiveops/autohelm

## Usage
### As standalone shell command
- Usage: autohelm [OPTIONS] COMMAND [ARGS]...
- Options:
    * `--help`  Show this message and exit.
    * `--log-level=TEXT` Set the log level for autohelm (defaults to `INFO`. Set to `DEBUG` for more details including helm commands)
- Commands:
  * `plot FILE`: Runs helm based on specified yaml file (see configuration example below)
    * Options:
      * `--debug`: Pass --debug to helm
      * `--dry-run`: Pass --dry-run to helm so no action is taken. Also includes `--debug`
  * `generate`: Generates example file `course.yml` with extensive descriptions
  * `version`: Output autohelm version
### As helm plugin
- Usage: helm autohelm [OPTIONS] COMMAND [ARGS]...
- Options:
    --help  Show this message and exit.
- Commands:
  * `plot`: Runs helm based on yaml file descriptors
  * Argument:
    - file: YAML file with description of charts to load
  * `generate`: Generates example file `course.yml` with extensive descriptions
  * `version`: Output autohelm version

## Example configuration file:
```
namespace: kube-system #namespace to install the chart in, defaults to 'kube-system'
repository: stable #repository to download chart from, defaults to 'stable'
repositories:
  incubator:
    url: https://kubernetes-charts-incubator.storage.googleapis.com
  stable:
    url: https://kubernetes-charts.storage.googleapis.com
charts: # list of charts
# chart_name: # chart name must match
#   version: version to install, defaults to latest. If a git repository is used, this is a branch/tag/ref.
#   repository: repository to download chart from, overrides above value
#     name: Optional, name of repository. If 'git' is used, must match the
#     url: Optional if repository is listed above. Url of repository to add if not already included in above repositories section
#     git: Git url where chart exists. Supercedes url argument
#     path: Path where chart is in git repository. If the chart is at the root, leave blank
#   namespace: namespace to install chart in, overrides above value
#   values: # key-value pairs to pass in using the helm --set argument. Inspect individual charts to determine which keys are available and should be set
#     key: value
  kubernetes-dashboard:
    version: "0.4.1"
  cluster-autoscaler:
    version: "0.2.1"
    values:
      autoscalingGroups[0].name: nodes
      autoscalingGroups[0].maxSize: 10
      autoscalingGroups[0].minSize: 1
  my-local-chart:
    repository: .
    values-strings:
      must-be-a-string: "1"
  heapster:
    version: "0.2.1"
  datadog:
    version: "0.8.2"
    repository: stable
    values:
      datadog.apiKey: notthekey
  spotify-docker-gc:
    version: "0.1.0"
  external-dns:
    version: "0.3.0"
  fluentd-cloudwatch:
    repository:
      name: incubator
    version: "0.1.1"
  centrifugo:
    repository:
      git: https://github.com/kubernetes/charts.git
      path: stable
    version: aaaf98b

```
