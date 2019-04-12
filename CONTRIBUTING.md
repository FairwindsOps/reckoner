# Contributing


## Installation for Local Development

Requirements
* Python 3.7
* pip3
* VirtualEnv

```
%> virtualenv venv
%> source ./venv/bin/activate
(venv) %> pip install .
```

## Requirements for Pull Requests
* Update the changelog
* Run tests
* Suggest version bump type

## How to run tests and test coverage
```bash
>> pip install -r development-requirements.txt
>> pytest reckoner/
```

With Coverage Reports
```bash
>> pytest --cov
>> pytest --cov reckoner/ --cov-report=html #shows an html line coverage report in ./htmlcov/
>> pytest --cov reckoner/ --cov-report=term #shows terminal coverage report of % coverage
```
