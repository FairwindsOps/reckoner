# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [0.13.0] UNRELEASED

### Fixed
- `version` command is fixed
- `generate` command is removed (was broken for several versions)

### Changes
- Adjusted schema to support `set` option for charts
  - This will translate all elements into `--set key=value` for the helm run
  - Current behavior actually does this for `values: {}`
  - All `values:` uses will warn that future versions will be type strong

## [0.12.0]

### Deprecated

Removing support for use as a helm plugin.

## [0.11.1]

### Fixed
- output when minimum versions are not met is no longer a stacktrace
- Fixes #40

## [0.11.0]

### Added
- Ensure chart dependencies are up to date with `helm dependency update` before installing it

## [0.10.3]

### Fixed
- Issue preventing values files from working.  #43

## [0.10.2]

### Fixed
- fixing error were value-strings from the course where not being set as set-string on the command line
- improved output when a desired environment variable is not set
- no longer adding the helm_args from course.yml twice

## [0.10.1]

CVE recommended fix

### Notes
Updated PyYAML required version to address active CVE

## [0.10.0]

Major-ish refactor to class structure and testing of independent classes in code. More work will be coming to make test coverage better.

### Added
- Default arguments for helm now do the right thing if using global flags for connecting to tiller (`tiller-namespace`, etc)

### Fixed
- Bubbled up actual error messages from Helm commands if they have a non-zero exit code

### Breaking Changes
- None expected but this is a refactor of the helm client interface

### Notes
Found several bugs that are noted in code and here. Fixes will be forthcoming.
- Found that rollback functionality isn't operational
- Found that dependency_update is non-operational
- Found that kubectl context update isn't functional

## [0.9.1]

### Fixed
- bug where string values were being set as `set-string`


## [0.9.0]

### Added

- the ability to specify helm_args in course.yml

### Breaking changes

- None, however the --debug flag will be deprecated in later versions. Warnings are added.

### Fixed

- numerous code formatting and spelling issues

## [0.8.4]

### Fixed
- better logging output for hooks
- added standard out logging for all helm commands

## [0.8.3]

### Fixed
- formating of the helm string that was broken by recent rebase
- context setting in the course and overidable by chart

## [0.8.2]
### Fixed
- environment variable interpolation
- fix namespace override at chart level

## [0.8.1]
### Fixed
- Nested values not being converted to strings properly
- Namespaces not being handled properly

### Updated
- Error handling during chart install

## [0.8.0]

### Added
- mock reset so tests will pass again after adding helm.help call

### Updated
- Improved error handling around helm binary
- `plot` process to it actually installs the charts


## [0.7.2]

### Deprecated
  Autohelm

### Updated
   Major refactor from a scripty based version to a modular object version

### Added
    Lots of Unit Testing


## [0.6.5]
### Added
- `--helm-args` flag to pass flags and params on to helm

### Updated
- swapped the order of evaluation of the --debug and --dryrun flags to prevent --dryrun from getting lost if both flags are set


## [0.6.4]
### Added
- Upload to PyPi

## [0.6.3]
### Fixed
- issue where chart dependencies/requirements were not being updated
- issue where helm release would be rolled back even when using --dry-run

## [0.6.2]
### Fixed
- issue where tags were not being pulled properly
- Description in setup.py

### Updated
- how branches are pulled with the chart is at the root of the repository

## [0.6.1]
### Fixed
- missing semver in setup.py
- removed trailing whitespace

## [0.6.0]
### Added
- minimum_version block to course.yml to define the mininum versions of `helm` and `autohelm` required by the course.yml
- --local-development flag

### Fixed
- improve logic for git sparse check out and chart path

## [0.5.1]
### Added
- support for yaml lists in the course.yml

### Fixed
- parsing of yaml dictionaries where it would only set the first value from the dictionary

## [0.5.0]
### Added
- pre_install and post_install hooks. Hooks are run at a per chart level
- `--heading` option to run a single chart from course.yaml

### Updated
- allow `values` block in course.yml to accept nested values

## [0.3.0]
### Added
- Support for `--set-string` option in helm 2.9.0+. Any keys under `values-string` in your course.yml will be passed to helm using `--set-string`
- `--dry-run` and `--debug` options for `autohelm plot` that pass identical options to helm

## [0.2.2]
### Fixed
- Missing environment variables are now treated as an error

## [0.2.1]
### Fixed
- bug where if a path was included in the course.yml, but the chart was at the root of the repo, sparse checkout would fail and the configured sparse-checkout file would poison the cache for that chart repository.

## [0.1.5]
### Added
- `files` to the course.yml to use yml files

### Fixed
- Maintain order of values during yaml load so that `--set` for lists remain ordered

## [.1.3] - 2018-2-22

### Added
- Ability to name releases something other than just the chart name

## [0.1.0] - 2018-1-26
Initial open-source commit
