# Contributing


## Installation for Local Development

Requirements
* Python 3
* pip

```shell
%> python -V                   # Check your version of python
%> python -m venv venv        # setup a virtual env in your cloned repo
%> source ./venv/bin/activate  # use the virtual env
(venv) %> pip install -e .     # Installs reckoner as locally linked folders
(venv) %> reckoner --version   # Check the version you're running in the virtualenv
```
Note that some of the above commands may need `python3` instead of just `python` to work depending on your environment.

## Requirements for Pull Requests
* Update the changelog
* Run tests
* Suggest version bump type

## How to run tests and test coverage
```bash
>> pip install -r development-requirements.txt
>> pytest
```

With Coverage Reports
```bash
>> pytest --cov reckoner/ --cov-report=html #shows an html line coverage report in ./htmlcov/
>> pytest --cov reckoner/ --cov-report=term #shows terminal coverage report of % coverage
```

## Releases
Create a GitHub release off of the master branch when you're ready to cut a final release. Please check the [CHANGELOG.md](./CHANGELOG.md) for relevant changes and how to semver bump your release. Also make sure your version conforms to semver standards (vX.Y.Z).
