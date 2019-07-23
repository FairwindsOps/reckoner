# reckoner [![CircleCI](https://circleci.com/gh/reactiveops/reckoner.svg?style=svg)](https://circleci.com/gh/reactiveops/reckoner) [![codecov](https://codecov.io/gh/reactiveops/reckoner/branch/master/graph/badge.svg)](https://codecov.io/gh/reactiveops/reckoner)

Command line helper for helm.
This utility adds to the functionality of [Helm](https://github.com/kubernetes/helm) in multiple ways:
* Creates a declarative syntax to manage multiple releases in one place
* Allows installation of charts from a git commit/branch/release

**Want to learn more?** ReactiveOps holds [office hours on Zoom](https://zoom.us/j/242508205) the first Friday of every month, at 12pm Eastern. You can also reach out via email at `opensource@fairwinds.com`

## Requirements
- python 3
- helm: installed and initialized

*Note:* Python2 is no longer supported by Reckoner. In general we suggest using the binary on the [Releases](https://github.com/reactiveops/reckoner/releases) page.

### Installation
Via Binary: *preferred method*
* Binary downloads of Reckoner client can be found on the [Releases](https://github.com/reactiveops/reckoner/releases) page.
* Unpack the binary `chmod +x` and add it to your PATH and you are good to go!

Via pip:
```shell
pip install reckoner
```

Via Git
```shell
pip install git+https://github.com/reactiveops/reckoner@master
```

For development see [CONTRIBUTING.md](./CONTRIBUTING.md).

## Quickstart

In course.yaml, write:
```yaml
charts:
  grafana:
    namespace: grafana
    set-values:
      image:
        tag: 6.2.5
  polaris-dashboard:
    namespace: polaris-dashboard
    repository:
      git: https://github.com/FairwindsOps/charts
      path: stable
    chart: polaris
```

Then run:
```bash
reckoner plot course.yaml
```

Grafana and Polaris should now be installed on your cluster!

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
  * `generate`: Generates example file `course.yml` with extensive descriptions
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

In-line values overrides for this chart. By default these are set using `--set`.  This introduces some interesting behavior.  Make sure to read the [Caveats](#caveats)

### values-strings

This is a wrapper around the helm functionality `--set-string`.  Allows the specification of variables that would normally be interpreted as boolean or int as strings.

```
charts:
  chartname:
    values:
      some.value: test
    values-strings:
      some.value.that.you.need.to.be.a.string: '1'
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

## Contributing
* [Code of Conduct](CODE_OF_CONDUCT.md)
* [Roadmap](ROADMAP.md)
* [Contributing](CONTRIBUTING.md)
