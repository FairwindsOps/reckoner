# Reckoner Documentation

## Course YAML Definition
The "course" is the definition of charts you wish to install using Reckoner. It consists of settings that tell Reckoner how to use helm to install your charts, in which namespaces and with what values. The course also outlines what remote chart repositories you'd like to be able to pull charts from. We fully expect the course file to be checked into your code repositories and managed as you would manage any other infrastructure as code.

We'll be breaking this documentation down into sections to make reference easier. We'll be starting by looking at top level definitions in your course YAML and breaking down into the lower level objects that make up the course. Keys will be denoted as required, otherwise they are optional.

# Top Level Keys
- `namespace` _(string)_ _**(required)**_  
    The default namespace for any chart definitions in your course
- `charts` _(object)_ _**(required)**_  
    The charts and chart definitions to install with this course, must be alphanumeric between 1 and 63 characters (also allows underscore and dash)
- `repositories` _(object)_  
    The definition of remote chart repositories available to this course
- `minimum_versions` _(object)_  
    The minimum helm and reckoner versions required to run this course
- `repository` _(string)_  
    The default remote repository for charts in this course if one is not defined in the chart definition
- `context` _(string)_  
    The `kubectl` context to use for this course (found with `kubectl get current-context`)
- `_references` _(object)_  
    An area in which you can put repeat code to be used throughout your course YAML. (See [this article on anchors](https://medium.com/@kinghuang/docker-compose-anchors-aliases-extensions-a1e4105d70bd))
- `helm_args` _(string)_  
    The default helm arguments to provide to any helm command run by Reckoner in this course

Example:
```yaml
namespace: kube-system
context: my-kube-cluster
repositories:
  stable:
    url: https://kubernetes-charts.storage.googleapis.com
charts:
  my-metrics-server: # See below for chart schema
    repository: stable
    chart: metrics-server
```

## Charts
The `charts` block in your course define all the charts you'd like to install and the values that the chart should be installed with. The `key` of your chart definition is the name (`release-name`) that Reckoner will ask helm to install under. Release names only allow alphanumerics, underscores and dashes and must be between 1 and 63 characters long.

- `namespace` _(string)_  
    The namespace in which to install this chart (overrides root level `namespace` definition)
- `chart` _(string)_  
    The name of the chart in the remote chart respository (example: `nginx-ingress`) and when using git repositories this is the folder in which the chart files exist
- `repository` _(string)_ or _(object)_  
    The name of the remote chart repository defined in the root level of your course (example: `stable`) and also can be passed a repository definition (like in the root key `repositories`)
- `version` _(string)_  
    The version of the chart in the remote chart repository (NOTE: When using a git repository, this is translated into the `ref` in the git repository, either commit SHA or tag name)
- `hooks` _(object)_  
    Allows `pre_install` and `post_install` which can be a string or a list of strings to execute in the shell around your chart installation (execution working directory is relative to your course file)
- `files` _(list of strings)_  
    Translates into `-f filename` for the helm install command line arguments (files are pathed relative to your course file)
- `values` _(object)_  
    Translates into a direct YAML values file for use with `-f <tmpfile>` for the helm install command line arguments
- `set-values` _(object)_  
    Translates all key-values into `--set` values for the helm install command line arguments
- `values-strings` _(object)_  
    Translates all key-values into `--set-string` values for the helm install command line arguments
- `plugins` _(string)_  
    Prepend your helm commands with this `plugins` string (see [PR 99](https://github.com/FairwindsOps/reckoner/pull/99))

```yaml
...
charts:
  my-release-name:
    chart: ngixn-ingress
    version: "0.25.1"
    repository: stable
    hooks:
      pre_install: echo hi
      post_install:
        - echo finished
        - echo ":)"
    values:
      set: these
      values:
        - for
        - me
        - please
...
```

## Repositories
This block defines all the remote chart repositories available for use in this course file. This definition can be used in the root level `repositories` block, or in the chart level `repository` block definition. NOTE: It cannot be used in the root level `repository` definition.

Keys:
- `url` _(string)_  
    The URL of the http chart repository
- `git` _(string)_  
    The git endpoint from which to pull the chart, in SSH or HTTP form (i.e. `git@github.com:FairwindsOps/charts.git`)
- `path` _(string)_ _**git specific**_  
    The path in the remote git chart repository in which to find the chart (i.e. `stable`)
- `name` _(string)_  
    The name to use for this remote chart repository in `helm repo list`, if not defined then the key of the definition is used

Repositories definitions support both HTTP and GIT endpoints for pulling charts. Below are the two supported schemas for each implementation.

### URL Based Chart Repository
```yaml
...
repositories:
  stable:
    url: https://kubernetes-charts.storage.googleapis.com
...
```
### Git Based Chart Repository
When using git repositories, the behavior of the `chart` and `version` fields change in the charts block. The `chart` becomes the folder in which the chart lives and `version` becomes the git ref (commit sha or tag or branch name).
```yaml
...
repositories:
  fairwinds-stable:
    git: https://github.com/FairwindsOps/charts
    path: stable
...
charts:
  polaris-dashboard:
    namespace: polaris-dashboard
    repository: fairwinds-stable
    chart: polaris # git folder
    version: f0af192d4eaa57bd0a79602f90e448bf23d89581 # SHA, branch or tag name
...
```

## Minimum Versions
- `reckoner` _(string)_  
    The minimum version of reckoner for this course to work properly (in semver notation).
- `helm` _(string)_
    The desired version of helm to run this course with (will fail if `helm` in your path is older than the version specified).

```yaml
...
minimum_versions:
  helm: 2.14.3
  reckoner: 2.1.0
```


# CLI Usage

```text
Usage: reckoner [OPTIONS] COMMAND [ARGS]...

Options:
  --version         Show the version and exit.
  --log-level TEXT  Log Level. [INFO | DEBUG | WARN | ERROR]. (default=INFO)
  --help            Show this message and exit.

Commands:
  plot     Install charts with given arguments as listed in yaml file...
  version  Takes no arguments, outputs version info
```

You can add `--help` to any `Command` and get output like the one below:
```text
$> reckoner plot --help

Usage: reckoner plot [OPTIONS] COURSE_FILE

  Install charts with given arguments as listed in yaml file argument

Options:
  --dry-run                      Pass --dry-run to helm so no action is taken.
                                 Implies --debug and skips hooks.
  --debug                        DEPRECATED - use --dry-run instead, or pass
                                 to --helm-args
  -o, --only, --heading <chart>  Only run a specific chart by name
  --helm-args TEXT               Passes the following arg on to helm, can be
                                 used more than once. WARNING: Setting this
                                 will completely override any helm_args in the
                                 course. Also cannot be used for configuring
                                 how helm connects to tiller.
  --continue-on-error            Attempt to install all charts in the course,
                                 even if any charts or hooks fail to run.
  --help                         Show this message and exit.
```
