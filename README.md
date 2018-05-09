
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
      * `--heading <chart>`: Run only the specified chart out of the course.yml
      * `--local-development`: Run `autohelm` in local-development mode where Tiller is not required and no helm commands are run. Useful for rapid or offline development.
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

There is an example file in autohelm/example-course.yml

Further customization is documented below.

# Options

## Global Options

### namespace

The default namespace to deploy into.  Defaults to kube-system

### repository

Repository to download chart from, defaults to 'stable'

### repositories

Where to get charts from.  We recommend at least the stable and incubator charts.

```
repositories:
  incubator:
    url: https://kubernetes-charts-incubator.storage.googleapis.com
  stable:
    url: https://kubernetes-charts.storage.googleapis.com
```

## Options for Charts

### values

In-line values overrides for this chart. By default these are set using `--set`.  This introduces some interesting behavior.  Make sure to read the [Caveats](#caveats)

### files

Use a values file(s) rather than leaving them in-line:

```
charts:
  chart_name:
    files:
      - /path/to/values/file.yml
```

### namespace

Override the default namespace.

### hooks

Hooks are run locally. For complex hooks, use an external script or Runner task.

```
charts:
  chart_name:
      pre_install:
        - ls
        - env
      post_install:
        - rm testfile
        - cp file1 file2
```

### version

The version of the chart to use

## Repository Options

### name

Optional, name of repository. If 'git' is used, must match.

### url

Optional if repository is listed above. Url of repository to add if not already included in above repositories section.

### git

Git url where chart exists. Supercedes url argument

### path

Path where chart is in the git repository.  NOTE: If the chart folder is in the root, leave this blank.

```
charts:
  chart_name: # chart name must match
    repository: repository to download chart from, overrides global value
      name: Optional, name of repository. If 'git' is used, must match the
      url: Optional if repository is listed above. Url of repository to add if not already included in above repositories section
      git: Git url where chart exists. Supercedes url argument
      path: Path where chart is in git repository. If the chart is at the root, leave blank
    namespace: namespace to install chart in, overrides above value
```

## Caveats

### Escaping

Keys and Values that have dots in the name need to be escaped.  Have a look at the [helm docs](https://github.com/kubernetes/helm/blob/master/docs/using_helm.md#the-format-and-limitations-of---set) on escaping complicated values.

Example:

```
charts:
  grafana:
    namespace: grafana
    values:
      datasources:
        datasources\.yaml:
          apiVersion: 1
```

The alternative is to use the files method described above
