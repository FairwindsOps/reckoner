#!/usr/bin/env python
# -- coding: utf-8 --

# Copyright 2017 Reactive Ops Inc.
#
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import coloredlogs
import click
import shutil
from reckoner import Reckoner, call
import pkg_resources

from meta import __version__


@click.group(invoke_without_command=True)
@click.version_option(__version__)
@click.option("--log-level", default="INFO", help="Log Level. [INFO | DEBUG | WARN | ERROR]. (default=INFO)")
@click.pass_context
def cli(ctx, log_level, *args, **kwargs):
    coloredlogs.install(level=log_level)
    pass


@cli.command()
@click.pass_context
@click.argument('file', type=click.File('rb'))
@click.option("--dry-run", is_flag=True, help="Pass --dry-run to helm so no action is taken")
@click.option("--debug", is_flag=True, help="Pass --debug to helm")
@click.option("--heading", "--only", metavar="<chart>", help="Only run a specific chart by name", multiple=True)
@click.option("--helm-args", help="Passes the following arg on to helm, can be used more than once", multiple=True)
@click.option("--local-development", is_flag=True, default=False, help="Run `reckoner` in local-development mode where Tiller is not required and no helm commands are run. Useful for rapid or offline development.")
def plot(ctx, file=None, dry_run=False, debug=False, only=None, helm_args=None, local_development=False):
    """ Install charts with given arguments as listed in yaml file argument """
    h = Reckoner(file=file, dryrun=dry_run, debug=debug, helm_args=helm_args, local_development=local_development)
    h.install(only)


@cli.command()
@click.pass_context
def generate(ctx):
    """ Takes no arguements, outputs an example plan """
    logging.info('Generating exampl course as course.yml')
    src = pkg_resources.resource_string("reckoner", "example-course.yml")
    logging.debug(src)
    with open("./course.yml", "w") as course_file:
        course_file.write(src)


@cli.command()
@click.pass_context
def version(ctx):
    """ Takes no arguements, outputs version info"""
    print(reckoner.__version__)
