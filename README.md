<div align="center">
  <img src="/docs/logo.svg" height="120" alt="Reckoner" style="padding-bottom: 20px" />
  <br><br>

  [![CircleCI](https://circleci.com/gh/FairwindsOps/reckoner.svg?style=svg)](https://circleci.com/gh/FairwindsOps/reckoner) [![codecov](https://codecov.io/gh/FairwindsOps/reckoner/branch/master/graph/badge.svg)](https://codecov.io/gh/FairwindsOps/reckoner)
</div>

Command line helper for helm.
This utility adds to the functionality of [Helm](https://github.com/kubernetes/helm) in multiple ways:
* Creates a declarative syntax to manage multiple releases in one place
* Allows installation of charts from a git commit/branch/release

**Want to learn more?** Fairwinds holds [office hours on Zoom](https://zoom.us/j/242508205) the first Friday of every month, at 12pm Eastern. You can also reach out via email at `opensource@fairwinds.com`

## Requirements
- python 3
- helm: installed and initialized

*Note:* Python2 is no longer supported by Reckoner. In general we suggest using the binary on the [Latest Releases](https://github.com/FairwindsOps/reckoner/releases/latest) page.

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
reckoner plot course.yaml
```

Grafana and Polaris should now be installed on your cluster!

## More Documentation
More advanced usage docs and course definition information can be found in the [docs/](/docs) folder of this repository.

## Contributing
* [Code of Conduct](CODE_OF_CONDUCT.md)
* [Roadmap](ROADMAP.md)
* [Contributing](CONTRIBUTING.md)
