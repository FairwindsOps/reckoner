#!/usr/bin/env python
# -- coding: utf-8 --

# Copyright 2017 Reactive Ops Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import coloredlogs
import click
from .reckoner import Reckoner
from . import exception
from .meta import __version__


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
@click.argument('course_file', type=click.File('rb'))
@click.option("--dry-run", is_flag=True, help='Pass --dry-run to helm so no action is taken. Implies --debug and '
                                              'skips hooks.')
@click.option("--debug", is_flag=True, help='DEPRECATED - use --dry-run instead, or pass to --helm-args')
@click.option("--only", "--heading", "-o", "only", metavar="<chart>", help='Only run a specific chart by name', multiple=True)
@click.option("--helm-args", help='Passes the following arg on to helm, can be used more than once. WARNING: Setting '
                                  'this will completely override any helm_args in the course. Also cannot be used for '
                                  'configuring how helm connects to tiller.', multiple=True)
@click.option("--continue-on-error", is_flag=True, default=False,
              help="Attempt to install all charts in the course, even if any charts or hooks fail to run.")
def plot(ctx, course_file=None, dry_run=False, debug=False, only=None, helm_args=None, continue_on_error=False):
    """ Install charts with given arguments as listed in yaml file argument """
    try:
        r = Reckoner(course_file=course_file, dryrun=dry_run, debug=debug, helm_args=helm_args, continue_on_error=continue_on_error)
        # Convert tuple to list
        only = list(only)
        r.install(only)
        if r.results.has_errors:
            click.echo(click.style("⛵🔥 Encountered errors while running the course ⛵🔥", fg="bright_red"))
            for result in r.results.results_with_errors:
                click.echo(click.style("\n* * * * *\n", fg="bright_red"))
                click.echo(click.style(str(result), fg="bright_red"))
            ctx.exit(1)
    except exception.ReckonerException as err:
        # This handles exceptions cleanly, no expected stack traces from reckoner code
        click.echo(click.style("Unexpected Error Occurred within Reckoner", fg="red"))
        click.echo(click.style("{}".format(err)))
        ctx.exit(1)


@cli.command()
def version():
    """ Takes no arguments, outputs version info"""
    print(__version__)
