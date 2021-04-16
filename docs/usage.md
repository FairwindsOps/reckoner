# Reckoner Documentation

## Course YAML Definition
The "course" is the definition of charts you wish to install using Reckoner. It consists of settings that tell Reckoner how to use helm to install your charts, in which namespaces and with what values. The course also outlines what remote chart repositories you'd like to be able to pull charts from. We fully expect the course file to be checked into your code repositories and managed as you would manage any other infrastructure as code.

We'll be breaking this documentation down into sections to make reference easier. We'll be starting by looking at top level definitions in your course YAML and breaking down into the lower level objects that make up the course. Keys will be denoted as required, otherwise they are optional.

# Top Level Keys
- `namespace` _(string)_ _**(required)**_
    The default namespace for any chart definitions in your course
- `namespace_management` _(object)_ **(optional)** a structure the defines default annotations and labels to the namespaces that Reckoner will create
- `charts` _(object)_ _**(required)**_
    The charts and chart definitions to install with this course, must be alphanumeric between 1 and 63 characters (also allows underscore and dash)
- `hooks` _(object)_
    Allows `init`, `pre_install`, and `post_install` which can be a string or a list of strings to execute in the shell around your chart installation (execution working directory is relative to your course file)
    - `init` after the course file is parsed, but before any other commands are executed
    - `pre_install` runs before any charts are install/upgraded. Only active for the `plot` subcommand.
    - `post_install` runs after all charts are install/upgraded successfully (unless `--continue-on-error` is set). Only active for the `plot` subcommand.
- `repositories` _(object)_
    The definition of remote chart repositories available to this course
- `minimum_versions` _(object)_
    The minimum helm and reckoner versions required to run this course
- `repository` _(string)_
    The default remote repository for charts in this course if one is not defined in the chart definition
- `context` _(string)_
    The `kubectl` context to use for this course (found with `kubectl config current-context`)
- `_references` _(object)_
    An area in which you can put repeat code to be used throughout your course YAML. (See [this article on anchors](https://medium.com/@kinghuang/docker-compose-anchors-aliases-extensions-a1e4105d70bd))
- `helm_args` _(list of strings)_
    The default helm arguments to provide to any helm command run by Reckoner in this course
- `secrets` _(list of objects)_
    A list of objects that define where and how to get secrets from your secret backend
    Required keys are `name` and `backend`.

Example:
```yaml
namespace: kube-system
namespace_management:
  default:
    metadata:
      annotations:
        ManagedBy: com.fairwinds.reckoner
      labels:
        labelName: labelValue
    settings:
      overwrite: True
context: my-kube-cluster
repositories:
  stable:
    url: https://kubernetes-charts.storage.googleapis.com
secrets:
- name: API_KEY
  backend: AWSParameterStore
  parameter_name: /path/to/api/key
  region: us-west-2
- name: APP_KEY
  backend: ShellExecutor
  script: |-
    cat ./secrets | grep app_key | base64
hooks:
  pre_install:
    - ls ./
  post_install:
    - kubectl get namespaces
charts:
  my-metrics-server: # See below for chart schema
    repository: stable
    chart: metrics-server
```

## Charts
The `charts` block in your course define all the charts you'd like to install and the values that the chart should be installed with. The `key` of your chart definition is the name (`release-name`) that Reckoner will ask helm to install under. Release names only allow alphanumerics, underscores and dashes and must be between 1 and 63 characters long.

- `namespace` _(string)_
    The namespace in which to install this chart (overrides root level `namespace` definition)
- `namespace_management` _(object)_ **(optional)** a structure the defines default annotations and labels to the namespace that Reckoner will create. Structure matches the `default` structure at the top level `namespace_management` block.
- `chart` _(string)_
    The name of the chart in the remote chart repository (example: `nginx-ingress`) and when using git repositories this is the folder in which the chart files exist
- `repository` _(string)_ or _(object)_
    The name of the remote chart repository defined in the root level of your course (example: `stable`) and also can be passed a repository definition (like in the root key `repositories`)
- `version` _(string)_
    The version of the chart in the remote chart repository (NOTE: When using a git repository, this is translated into the `ref` in the git repository, either commit SHA or tag name)
- `hooks` _(object)_
    Allows `pre_install` and `post_install` which can be a string or a list of strings to execute in the shell around your chart installation (execution working directory is relative to your course file)
     - `pre_install` runs before the chart is installed/upgraded. Only active for the `plot` subcommand.
    - `post_install` runs after the chart is installed/upgraded successfully (unless `--continue-on-error` is set). Only active for the `plot` subcommand.
- `files` _(list of strings)_
    Translates into `-f filename` for the helm install command line arguments (files are pathed relative to your course file)
- `values` _(object)_
    Translates into a direct YAML values file for use with `-f <tmpfile>` for the helm install command line arguments
- `plugins` _(string)_
    Prepend your helm commands with this `plugins` string (see [PR 99](https://github.com/FairwindsOps/reckoner/pull/99))

```yaml
...
charts:
  my-release-name:
    chart: nginx-ingress
    version: "0.25.1"
    namespace: nginx-ingress
    namespace_management:
      metadata:
        annotations:
          foo: bar
        labels:
          boo: far
      settings:
        overwrite: false
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
    The path in the remote git chart repository in which to find the chart (i.e. `stable`). This will result in a git sparse checkout of `${path}/${chart-name}`
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

## Namespace Management

When you wish to manage annotations or labels for the namespaces you are installing into with Reckoner, this `namespace_management` block to define default namespace metadata and the whether or not it should overwrite the values that exist.

`namespace_management` blocks can be defined at the top level or at the chart level. By default, the top level `default` metadata will be used for all namespaces and any `metadata.annotations` or `metadata.labels` set in the charts will be additive. However, if `settings.overwrite` is `True` then the `metadata` block from the chart will replace any matching labels or annotation values.

Keep in mind, chart level `metadata` properties _cannot_ remove or delete any course level properties, only overwrite the value. For this reason, it's best if you don't set course level namespace metadata unless you truly want it applied to _all_ namespaces defined in this course.yml.

Example:
```yaml
namespace_management:
  default:
    metadata:
      annotations:
        ManagedBy: com.fairwinds.reckoner
      labels:
        labelName: labelValue
    settings:
      overwrite: True
```

## Secrets
  A list of maps that define how and where to get secret values to inject into the environment.

  Required Keys:
  * `name`: The name of the secret. Must match the target inline variable. For example if your `values` has a template variable `${PASSWORD}` the name must be `PASSWORD`

  * `backend`: Defines what secret provider to use to retreive the secrets value `backend` must be one of the Secret.ALLOWED_BACKENDS

  ### Currently Supported Backends:
  #### `AWSParameterStore`
  Retrieves value from the AWSParameterStore at the path specified. Decrypts Secure Strings:
  Required Arguments:
  * `parameter_name`: _(string)_ The path to the secrets
  Optional Arguemnts:
  * `region`: _(string)_ Region in which the secret is stored, if different from the $AWS_PROFILE configured

  #### `ShellExecutor`
  Runs a shell command and returns the output with with whitespace stripped.
  Required Arguments:
  * `script`: _(string)_  The script to run

# CLI Usage

```text
Usage: reckoner [OPTIONS] COMMAND [ARGS]...

Options:
  --version         Show the version and exit.
  --log-level TEXT  Log Level. [INFO | DEBUG | WARN | ERROR]. (default=INFO)
  --help            Show this message and exit.

Commands:
  plot           Install charts with given arguments as listed in yaml file argument
  template       Output the template of the chart or charts as they would be installed or
  upgraded
  get-manifests  Output the manifests of the chart or charts as they are installed
  diff           Output diff of the templates that would be installed and the manifests as they are installed
  update         Checks to see if anything will be changed, if so, update the release, if not, does nothing
  version  Takes no arguments, outputs version info
  import         Outputs a chart block that can be used to import the specified release
```

You can add `--help` to any `Command` and get output like the one below:
```text
$> reckoner plot --help
Usage: reckoner plot [OPTIONS] COURSE_FILE

  Install charts with given arguments as listed in yaml file argument

Options:
  --dry-run                       Pass --dry-run to helm so no action is
                                  taken. Implies --debug and skips hooks.

  --debug                         DEPRECATED - use --log-level=DEBUG as a
                                  parameter to `reckoner` instead. May be used
                                  with or without `--dry-run`. Or, pass
                                  `--debug` to --helm-args

  -a, --run-all                   Run all charts in the course. Mutually
                                  exclusive with 'only'.

  -o, --only, --heading <chart>   Only run a specific chart by name Mutually
                                  exclusive with 'run_all'.

  --helm-args TEXT                Passes the following arg on to helm, can be
                                  used more than once. WARNING: Setting this
                                  will completely override any helm_args in
                                  the course. Also cannot be used for
                                  configuring how helm connects to tiller.

  --continue-on-error             Attempt to install all charts in the course,
                                  even if any charts or hooks fail to run.

  --create-namespace / --no-create-namespace
                                  Will create the specified nameaspace if it
                                  does not already exist. Replaces
                                  functionality lost in Helm3

  --log-level TEXT                Log Level. [INFO | DEBUG | WARN | ERROR].
                                  (default=INFO)

  --help                          Show this message and exit.
```

Or
```
# reckoner update --help
Usage: reckoner update [OPTIONS] COURSE_FILE

  Checks to see if anything will be changed, if so, update the release,
  if not, does nothing

Options:
  --dry-run                       Pass --dry-run to helm so no action is
                                  taken. Implies --debug and skips hooks.

  --debug                         DEPRECATED - use --log-level=DEBUG as a
                                  parameter to `reckoner` instead. May be used
                                  with or without `--dry-run`. Or, pass
                                  `--debug` to --helm-args

  -a, --run-all                   Run all charts in the course. Mutually
                                  exclusive with 'only'.

  -o, --only, --heading <chart>   Only run a specific chart by name Mutually
                                  exclusive with 'run_all'.

  --helm-args TEXT                Passes the following arg on to helm, can be
                                  used more than once. WARNING: Setting this
                                  will completely override any helm_args in
                                  the course. Also cannot be used for
                                  configuring how helm connects to tiller.

  --continue-on-error             Attempt to install all charts in the course,
                                  even if any charts or hooks fail to run.

  --create-namespace / --no-create-namespace
                                  Will create the specified nameaspace if it
                                  does not already exist. Replaces
                                  functionality lost in Helm3

  --log-level TEXT                Log Level. [INFO | DEBUG | WARN | ERROR].
                                  (default=INFO)

  --help                          Show this message and exit.
```

Or
```text
# reckoner template --help
Usage: reckoner template [OPTIONS] COURSE_FILE

  Output the template of the chart or charts as they would be installed or
  upgraded

Options:
  -a, --run-all                  Run all charts in the course. Mutually
                                 exclusive with 'only'.

  -o, --only, --heading <chart>  Only run a specific chart by name. Mutually
                                 exclusive with 'run_all'.

  --helm-args TEXT               Passes the following arg on to helm, can be
                                 used more than once. WARNING: Setting this
                                 will completely override any helm_args in the
                                 course. Also cannot be used for configuring
                                 how helm connects to tiller.

  --log-level TEXT               Log Level. [INFO | DEBUG | WARN | ERROR].
                                 (default=INFO)

  --help                         Show this message and exit.
```
Or
```text
# reckoner import --help
Usage: reckoner import [OPTIONS]

  Outputs a chart block that can be used to import the specified release

Options:
  --log-level TEXT     Log Level. [INFO | DEBUG | WARN | ERROR].
                       (default=INFO)

  --release_name TEXT  The release name to import  [required]
  --namespace TEXT     The namespace of the release  [required]
  --repository TEXT    The repository of the chart  [required]
  --help               Show this message and exit.
```
