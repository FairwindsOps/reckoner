<div align="center">
  <img src="/docs/logo.svg" height="120" alt="Reckoner" style="padding-bottom: 20px" />
  <br><br>

  [![CircleCI](https://circleci.com/gh/FairwindsOps/reckoner.svg?style=svg)](https://circleci.com/gh/FairwindsOps/reckoner) [![codecov](https://codecov.io/gh/FairwindsOps/reckoner/branch/master/graph/badge.svg)](https://codecov.io/gh/FairwindsOps/reckoner)
</div>

Command line helper for helm.
This utility adds to the functionality of [Helm](https://github.com/kubernetes/helm) in multiple ways:

* Creates a declarative syntax to manage multiple releases in one place
* Allows installation of charts from a git commit/branch/release

**Want to learn more?** Reach out on [the Slack channel](https://fairwindscommunity.slack.com/messages/reckoner) ([request invite](https://join.slack.com/t/fairwindscommunity/shared_invite/zt-e3c6vj4l-3lIH6dvKqzWII5fSSFDi1g)), send an email to `opensource@fairwinds.com`, or join us for [office hours on Zoom](https://fairwindscommunity.slack.com/messages/office-hours)

## Requirements

* python 3
* helm (>= 3.0.0), installed and initialized

*Note:* Python2 is no longer supported by Reckoner. In general we suggest using the binary on the [Latest Releases](https://github.com/FairwindsOps/reckoner/releases/latest) page.
*Note2:* Helm2 support will not be tested from v4.3.0. The maintainters have [deprecated helm2](https://helm.sh/blog/helm-v2-deprecation-timeline/).

### Installation

Via Binary: *preferred method*

* Binary downloads of the Reckoner client can be found on the [Releases](https://github.com/FairwindsOps/reckoner/releases) page.
* Unpack the binary, `chmod +x`, add it to your PATH, and you are good to go!

For development see [CONTRIBUTING.md](./CONTRIBUTING.md).

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

## More Documentation

More advanced usage docs and course definition information can be found in the [docs/](/docs) folder of this repository.

## Contributing

* [Code of Conduct](CODE_OF_CONDUCT.md)
* [Roadmap](ROADMAP.md)
* [Contributing](CONTRIBUTING.md)
