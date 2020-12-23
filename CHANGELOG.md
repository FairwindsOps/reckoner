# DEPRECATED - See the releases page for the changelog


# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## Unreleased
### Fixed
- bug where the helm client version check would fail for helm2 and never proceed to check helm3
- added create namespace functionality because they removed it from helm3
- removed beta warnings about Helm 3

## [2.2.0]
### Changes
- Added a warning message when using helm3: NOTE HELM3 IS NOT YET SUPPORTED! Use at your own peril!
- Added better logging for helm errors (into debug output)
- Added better handling of uninitialized helm (client side)
- Fixed issues where helm would try to interpolate variables in comments provided in `values: {}` section of a chart definition
- Added better logging for debug when unexpected errors happen in python
- Added better logging output for debugging yaml parse issues
- Fixed repository git support for defining git chart endpoints at the top level and chart level

## [2.1.1]
### Fixes
- Fixed issues with relative vs absolute paths on files used in course yamls

## [2.1.0]
### Breaking Changes
- Added Helm 3 detection and added a warning and documentation on helm 3 reckoner support blockers
- Schema Validation
    - We are introducing schema validation on the course.yml. This will exit hard if your course.yml has indentation errors or other issues that don't conform to the course.yml expected schema. The schema can be found at [here](/reckoner/assets/course.schema.json).
    - Reckoner now blocks on YAML duplicate keys. If your yaml has duplicate keys in any section of the yaml, the course will fail to load and no actions will be performed. There is no way to allow duplicate keys in course.yml anymore to avoid inconsistent behavior or unexpected course runs.
    - More details on the implications of schema validations can be found here: [docs/changelog_details/schema_validation.md](/docs/changelog_details/schema_validation.md).
    - As a part of defining a strict schema for course YAMLs, you will need to house any "reuable" YAML blocks in the top-level-key of `_references: {}`.


### Fixes
- Fixed the references for values to be relative: `files: []` now are referenced relative to the course yaml you're running. Also added end-to-end test for values files in subfolders.

## [2.0.0]
### Breaking Changes
- Changes to `values: {}` behavior:
  The chart: {values: {}} config block and chart: {set-values:{}} config block now have different behavior. set-values: {} always gets translated into helm arguments as --set key=value. The values: {} now gets applied to helm arguments as -f temporary_values_name.yml. The values: {} config block is now fully consistent with intended types and would behave as though you are using a -f my_values.yml in your helm command. Prior to this change you would see inconsistent type casting for float, bool and integer config settings. For more information on the behavior differences between `values`, `set-values`, and `values-strings` you can look at our [end to end testing test course.yml](/end_to_end_testing/test_strong_typing.yml).
- BUG FIX: Using `"null"`, `null`, `"Null"`, and `"NULL"` as values in `set-values: {}` will be interpreted as `null` (void of value) in the `--set` value. Previously, if you set `null` as the yaml value, you would get `--set key=None` due to python interpreting the value as `None` and thus would show up as `{"key": "None"}` in the helm values. This fix more closely aligns with expected behavior in helm.

## [1.4.0]
### Breaking Changes
- Removed the `--local-development` flag from `plot` command (unused) and cleaned up test dependencies
- Reckoner now has exit codes that reflect the state of the course run.
  Reckoner will immediately exit with a non-zero exit code when a chart or hook fails to run. Previous
  behavior to continue on error can be enabled by using the `--continue-on-error` flag on your `plot`.

## [1.3.0]
### Breaking Changes
Python2 support is now ended.  Pip install will now require python ~= 3.6.  In any case, use of the binary release is recommended.

## [1.2.0]
- Support helm wrapper plugins such as [Helm Secrets](https://github.com/futuresimple/helm-secrets)
- POTENTIAL BREAKING CHANGE: Refactored all helm commands to use `--arg value` instead of `--arg=value`. (This helps with poor param support with how helm plugin wrappers work)

## [1.1.6]
- Skipped versions to kickstart pipelines

## [1.1.4]
- Added pipeline to distribute binaries (no code changes)

## [1.1.3]
- Added support for pyinstaller builds for Linux and Darwin (for later binary distribution)

## [1.1.2]

### Changes
- Added fix for interpolated variables in kube specs (see #82)
- Adjusted help for plot (--heading / --only also accepts -o now)
- Updated underlying dependencies (click, semver, GitPython)

## [1.1.1]

### Changes
- Adjusted versioning to be based on git tag
- Added support for python 3.6 & 3.7 with CI checks
- Added end-to-end basic tests for CI (invocation regression testing)

## [1.1.0]

### Changes
- Upgraded to oyaml 0.8+

## [1.0.2]

### Fixed
* Fixed hook runner behavior: Previous to v1.0.0, the hooks would stop running
  after the first non-zero exit code. This behavior broke with some refactoring
* Added tests to catch run-hook behavior

## [1.0.1]

### Fixed
* Reckoner would silently fail when a --only or --heading was defined for a
  chart that didn't exist in your course.
  This behavior will still succeed if you provide at least one valid --heading
  value. If no values are in your course then this bubbles up an error
* Internal Fix: Reckoner Errors now are a single parent exception class
* Fixed hook output to user instead of hidden only in debug (#59)
* Fixed hooks to run from the same path as course.yml. This makes PWD relative
  to course.yml for easier groking of paths for hook pre/post install.

## [1.0.0]

### Fixed
- `version` command is fixed
- `generate` command is removed (was broken for several versions)

### Changes
- Adjusted schema to support `set` option for charts
  - This will translate all elements into `--set key=value` for the helm run
  - Current behavior actually does this for `values: {}`
  - All `values:` uses will warn that future versions will be type strong
- More testing for CLI contract options

### Deprecation Notice
In the future, the `values: {}` configuration of a chart will change it's
behavior (see Issue #7). The current behavior translates any `values:{}` into
`--set` for the command line helm. This makes certain object types lose their
type fidelity. This means `true` becomes `string("true")` when pushed through
`--set values=true`. To maintain the same behavior for your settings please
change `values:{}` to `set-values:{}`. This behavior deprecaton will start to
be enforces in later versions of Reckoner.

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
