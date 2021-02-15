# Reckoner

## Intent
Reckoner is intended to provide a declarative syntax to install and manage multiple Helm releases. A primary additional feature is the ability to pull from a git repository instead of a local chart or chart repository.

## Key Design Features

* A stable declarative syntax for Helm releases and their configuration values
* The ability to pull a chart from a git repository
* Pre and Post hooks to provide extra steps not included in the Helm chart installation

## Scope

### In Scope:
* Interaction with the Helm Client
* Translation of configuration to a helm command
* Staying up to date with Helm features and commands


### Out of Scope:
* Direct interaction with the Tiller api
* Replacing Tiller
* Creation or modification of Helm charts
* Overwriting portions of a chart's output (eg Kustomize or Ship)
* Managing installation versions of Helm and Tiller

## Golang Re-Write and Schema Changes

We will be rewriting this project in Go in order to provide a nicer UX via a pre-compiled binary. At the same time, the course file schema will be changed in order to facilitate this rewrite.

The re-write will occur in [This Pull Request](https://github.com/FairwindsOps/reckoner/pull/293). Any new branches related to the rewrite should come from here in the short term.

### Guiding principles of the re-write

- No new features will be added that are not directly related to the schema change
- Feature parity should be maintained
- The old end-to-end test suite must run with the new binary with minimal changes (pre-converting the schema may be necessary)
- A conversion path from the old schema to the new will be provided
- Unit Test coverage should be relatively high. I'm thinking >60%

### Un-answered Questions

- Should we automatically detect the old schema and convert it for the end-user?
- Should we instead just error and point them at the conversion utility?
- Do we care about ordering? If so, this may get much uglier. In the past we have maintained strict ordering of the releases.
- Can we import the helm packages instead of relying on exec to the installed helm binary?

### New Schema Changes

The new schema will align better with Go structs, rather than constantly using `map[string]interface`.

[See the new schema here, along with the conversion function](https://github.com/FairwindsOps/reckoner/blob/golang/pkg/course/course.go)

Some major changes to the functionality:

#### Repositories will _only_ be defined in the header

Each release will reference the name of the repository from the header section.

This includes git repositories. This should prevent confusion in the future, as well as allow us to not need a dynamic field in the release struct (or in the repositories section of the header)

#### Charts will be renamed Releases

This makes a lot more sense. It's what they are.
