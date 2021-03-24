<div align="center">
    <img src="img/reckoner-logo.svg" height="120" alt="Reckoner" style="padding-bottom: 20px" />
    <br>
    <a href="https://github.com/FairwindsOps/reckoner/releases">
        <img src="https://img.shields.io/github/v/release/FairwindsOps/reckoner">
    </a>
    <a href="https://join.slack.com/t/fairwindscommunity/shared_invite/zt-e3c6vj4l-3lIH6dvKqzWII5fSSFDi1g">
      <img src="https://img.shields.io/static/v1?label=Slack&message=Join+our+Community&color=4a154b&logo=slack">
    </a>
</div>

Command line helper for helm.

This utility adds to the functionality of [Helm](https://github.com/kubernetes/helm) in multiple ways:

* Creates a declarative syntax to manage multiple releases in one place
* Allows installation of charts from a git commit/branch/release

**Want to learn more?** Reach out on [the Slack channel](https://fairwindscommunity.slack.com/messages/reckoner) ([request invite](https://join.slack.com/t/fairwindscommunity/shared_invite/zt-e3c6vj4l-3lIH6dvKqzWII5fSSFDi1g)), send an email to `opensource@fairwinds.com`, or join us for [office hours on Zoom](https://fairwindscommunity.slack.com/messages/office-hours)


## Requirements

* python 3
* helm (>= 3.0.0), installed and initialized

*Note:* Python2 is no longer supported by Reckoner.
*Note2:* Helm2 support will not be tested from v4.3.0. The maintainers have [deprecated helm2](https://helm.sh/blog/helm-v2-deprecation-timeline/).

### Installation

* `pip install reckoner`

## Quickstart

In course.yaml, write:

```yaml
namespace: default
charts:
  grafana:
    namespace: grafana
    values:
      image:
        tag: "6.2.5"
  polaris-dashboard:
    namespace: polaris-dashboard
    repository:
      git: https://github.com/FairwindsOps/charts
      path: stable
    chart: polaris
```

Then run:

```shell
reckoner plot course.yaml --run-all
```

Grafana and Polaris should now be installed on your cluster!

## Adopting Reckoner

Warning: Experimental

If you're already using Helm but want to start using `reckoner`, you can use `reckoner import` to facilitate your migration.

We recommend carefully examining the output of a `reckoner diff` before relying on any imported course.yml definitions.
