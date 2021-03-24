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

*Note:* Python2 is no longer supported by this tool

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
