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

## Releases
Create a GitHub release off of the master branch when you're ready to cut a final release. Please check the [CHANGELOG.md](./CHANGELOG.md) for relevant changes and how to semver bump your release. Also make sure your version conforms to semver standards (vX.Y.Z).

## Building with PyInstaller
We support building reckoner with PyInstaller for easier binary style distribution (look mom, no virtualenv!).

Below are some instructions on how to build locally with PyInstaller:

```bash
# Check out the repo and activate your virtual environment!
source .venv/bin/activate
pip install pyinstaller setuptools-scm
pip install -e .
cd installer

# setup a static version file for pyinstaller to use for versioning
python -c 'from setuptools_scm import get_version; get_version(root="..", write_to="reckoner/version.txt")'
# NOTE you will need to run the above file *for every pyinstaller build!!*

# Create the binary
pyinstaller --noconfirm --paths .:../ --onefile --add-data ../reckoner/version.txt:reckoner --name reckoner cli.py

# Test your shiny new binary
./dist/reckoner version
```

Note that you can find this process in the `compile` section of the pipeline file for this repo.
