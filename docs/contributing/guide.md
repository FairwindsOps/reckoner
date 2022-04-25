---
meta:
  - name: description
    content: "Fairwinds Reckoner | Contribution Guidelines"
---
# Contributing


## Installation for Local Development

Requirements:
* [Go](https://go.dev)

```sh
$ go --version    # Check your version of golang
$ go mod tidy     # get dependencies
$ go run . --help # compile & run the project
```

## Requirements for Pull Requests
* Update the changelog
* Run tests
* Suggest version bump type

## How to run tests and test coverage
```sh
$ go test ./...
```
