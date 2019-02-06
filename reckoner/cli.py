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
from reckoner import Reckoner
import pkg_resources

from meta import __version__


@click.group(invoke_without_command=True)
@click.version_option(__version__)
@click.option("--log-level", default="INFO", help="Log Level. [INFO | DEBUG | WARN | ERROR]. (default=INFO)")
@click.pass_context
def cli(ctx, log_level, *args, **kwargs):
    coloredlogs.install(level=log_level)
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(1)
    pass


@cli.command()
@click.pass_context
@click.argument('file', type=click.File('rb'))
@click.option("--dry-run", is_flag=True, help='Pass --dry-run to helm so no action is taken. Implies --debug and '
                                              'skips hooks.')
@click.option("--debug", is_flag=True, help='DEPRECATED - use --dry-run instead, or pass to --helm-args')
@click.option("--heading", "--only", metavar="<chart>", help='Only run a specific chart by name', multiple=True)
@click.option("--helm-args", help='Passes the following arg on to helm, can be used more than once. WARNING: Setting '
                                  'this will completely override any helm_args in the course. Also cannot be used for '
                                  'configuring how helm connects to tiller.', multiple=True)
@click.option("--local-development", is_flag=True, default=False, help='Run `reckoner` in local-development mode '
                                                                       'where Tiller is not required and no helm '
                                                                       'commands are run. Useful for rapid or offline '
                                                                       'development.')
def plot(ctx, file=None, dry_run=False, debug=False, only=None, helm_args=None, local_development=False):
    """ Install charts with given arguments as listed in yaml file argument """
    h = Reckoner(file=file, dryrun=dry_run, debug=debug, helm_args=helm_args, local_development=local_development)
    h.install(only)


@cli.command()
def version():
    """ Takes no arguments, outputs version info"""
    print(__version__)
