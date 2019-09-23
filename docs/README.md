# Reckoner Documentation

## Course YAML Definition
The "course" is the definition of charts you wish to install using Reckoner. It consists of settings that tell Reckoner how to use helm to install your charts, in which namespaces and with what values. The course also outlines what remote chart repositories you'd like to be able to pull charts from. We fully expect the course file to be checked into your code repositories and managed as you would manage any other infrastructure as code.

We'll be breaking this documentation down into sections to make reference easier. We'll be starting by looking at top level definitions in your course YAML and breaking down into the lower level objects that make up the course. Keys will be denoted as required, otherwise they are optional.

### Top Level Keys
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

### Charts
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

### Repositories
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

#### URL Based Chart Repository
```yaml
...
repositories:
  stable:
    url: https://kubernetes-charts.storage.googleapis.com
...
```
#### Git Based Chart Repository
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

* * * 
## Extended Usage

### As standalone shell command
- Usage: reckoner [OPTIONS] COMMAND [ARGS]...
- Options:
    * `--help`  Show this message and exit.
    * `--log-level=TEXT` Set the log level for reckoner (defaults to `INFO`. Set to `DEBUG` for more details including helm commands)
- Commands:
  * `plot FILE`: Runs helm based on specified yaml file (see configuration example below)
    * Options:
      * `--debug`: Pass --debug to helm
      * `--dry-run`: Pass --dry-run to helm so no action is taken. Also includes `--debug`
      * `--heading <chart>`: Run only the specified chart out of the course.yml
      * `--continue-on-error`: If any charts or hooks fail, continue installing other charts in the course
      * `--helm-args <helm-arg>`: Pass arbitrary flags and parameters to all
        helm chart commands in your course.yml.  Example:
        `--helm-args --set=foo=toast`, or `--helm-args --recreate-pods`.
        Multiples are supported but only one parameter per `--helm-args` is
        supported. Note that specifying this flag will override `helm_args`
        in the course.yml file.
  * `version`: Output reckoner version

# Options

## Global Options

### namespace

The default namespace to deploy into.  Defaults to kube-system

### repository

Repository to download chart from, defaults to 'stable'

### context

Optional.  The kubectl cluster context to use for installing, defaults to the current context.

### repositories

Where to get charts from.  We recommend at least the stable and incubator charts.

```
repositories:
  incubator:
    url: https://kubernetes-charts-incubator.storage.googleapis.com
  stable:
    url: https://kubernetes-charts.storage.googleapis.com
```

### helm_args

A list of arguments to pass to helm each time reckoner is run. Arguments are
applied for every chart install in your course.  This cannot be used for args
that specify how Helm connects to the tiller.

```
helm_args:
  - --recreate-pods
```

## Options for Charts

### values

Override values file for this chart. By default these are translated into `-f temp_values_file.yml` when helm is run. This means that anything in the `values: {}` settings should keep it's YAML type consistency.

```yaml
charts:
  my-chart:
    values:
      my-string: "1234"
      my-bool: false
```

### set-values

In-line values overrides for this chart. By default these are translated into `--set key=value` which means that the default helm type casting applies. Helm will try to cast `key: "true"` into a `true` boolean value, as well as casting strings of integers into the integer representation, ie: `mystr: "1234"` becomes `mystr: 1234` when using `--set`.

```yaml
charts:
  my-chart:
    my-int: "1234"         # Converted into `int` when used with --set
    my-string: 1.05        # Float numbers are converted to strings in --set
    my-bool: "true"        # Strings of bool values are converted to bool in --set
    my-string-null: "null" # String of "null" get converted to null value in --set
    my-null: null          # null values are kept as null values in --set-strings
```

### values-strings

This is a wrapper around the helm functionality `--set-string`.  Allows the specification of variables that would normally be interpreted as boolean or int as strings.

```
charts:
  chartname:
    values:
      some.value: test
    values-strings:
      some.value.that.you.need.to.be.a.string: "1"
```

### files

Use a values file(s) rather than leaving them in-line:

```
charts:
  chart_name:
    files:
      - /path/to/values/file.yml
```
Note: The file paths will be interpreted as relative to the working directory of
the shell calling reckoner.

### namespace

Override the default namespace.

### hooks

Hooks are run locally. For complex hooks, use an external script or Runner task.

```
charts:
  chart_name:
    hooks:
      pre_install:
        - ls
        - env
      post_install:
        - rm testfile
        - cp file1 file2
```

### version

The version of the chart to use

### plugin

A helm wrapper plugin to invoke for this chart.
Make sure that the plugin is installed in your environment, and is working properly.
Unfortunately, we cannot support every plugin.

```
charts:
  chart_name:
    plugin: secrets
    files:
      - /path/to/secret/values/file.yaml
```

## Repository Options

### name

Optional, name of repository.

### url

Optional if repository is listed above. Url of repository to add if not already included in above repositories section.

### git

Git url where chart exists. Supercedes url argument

### path

Path where chart is in the git repository.  NOTE: If the chart folder is in the root, leave this blank.

```
charts:
  chart_name:
    repository: repository to download chart from, overrides global value
      name: Optional, name of repository.
      url: Optional if repository is listed above. Url of repository to add if not already included in above repositories section
      git: Git url where chart exists. Supercedes url argument
      path: Path where chart is in git repository. If the chart is at the root, leave blank
    namespace: namespace to install chart in, overrides above value
```

## Caveats
### Strong Typing
Using `set-values: {}` will cast null, bool and integers from strings even if they are quoted in the course.yml. This is the default Helm behavior for `--set`. Note also that floats will be cast as strings when using `set-values: {}`. Also note that if you're using environment variable replacements and you set `my-key: ${MY_VAR}`, if `MY_VAR=yes` then helm will use YAML 1.1 schema and make `my-key: true`. You need to quote your environment variables in order for `"yes"` to be cast as a string instead of a bool (`my-key: "${MY_VAR}"`).

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
