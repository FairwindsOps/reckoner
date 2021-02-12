#!/usr/bin/env python
# -- coding: utf-8 --

# Copyright 2017 FairwindsOps Inc.
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

import click
import logging
import traceback
import coloredlogs

from reckoner.importer import draft_release
from reckoner import exception
from reckoner.meta import __version__
from reckoner.reckoner import Reckoner
from reckoner.config import Config
from reckoner.yaml.handler import Handler as yaml

from reckoner.schema_validator.course import validate_course_file, lint_course_file


class Mutex(click.Option):
    def __init__(self, *args, **kwargs):
        self.not_required_if: list = kwargs.pop("not_required_if")

        assert self.not_required_if, "'not_required_if' parameter required"
        kwargs["help"] = (kwargs.get("help", "") + " Mutually exclusive with '" + ", ".join(self.not_required_if) + "'.").strip()
        super(Mutex, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        current_opt: bool = self.name in opts
        for mutex_opt in self.not_required_if:
            if mutex_opt in opts:
                if current_opt:
                    raise click.UsageError("Illegal usage: '" + str(self.name) + "' is mutually exclusive with '" + str(mutex_opt) + "'.")
                else:
                    self.prompt = None
        return super(Mutex, self).handle_parse_result(ctx, opts, args)


# Options and Arguments
course_file_argument = click.argument('course_file', type=click.File('rb'))

run_all_option = click.option("--run-all", "-a", "run_all", is_flag=True, help='Run all charts in the course.', cls=Mutex, not_required_if=["only"])
log_level_option = click.option("--log-level", default="INFO", help="Log Level. [INFO | DEBUG | WARN | ERROR]. (default=INFO)")
only_option = click.option("--only", "--heading", "-o", "only", metavar="<chart>", help='Only run a specific chart by name.', multiple=True, cls=Mutex,
                           not_required_if=["run_all"])
dry_run_option = click.option("--dry-run", is_flag=True, help='Pass --dry-run to helm so no action is taken. Implies --debug and '
                              'skips hooks.')
helm_args_option = click.option("--helm-args", help='Passes the following arg on to helm, can be used more than once. WARNING: Setting '
                                'this will completely override any helm_args in the course. Also cannot be used for '
                                'configuring how helm connects to tiller.', multiple=True)
continue_on_error_option = click.option("--continue-on-error", is_flag=True, default=False,
                                        help="Attempt to install all charts in the course, even if any charts or hooks fail to run.")

create_namespace_option = click.option("--create-namespace/--no-create-namespace", default=True,
                                       help="Will create the specified nameaspace if it does not already exist. Replaces functionality lost in Helm3")
update_repos_option = click.option("--update-repos/--no-update-repos", default=True,
                                   help="Will update Helm repos when --update-repos is specified [DEFAULT]. Skips update when --no-update-repos is specified.")

# DEPRECATED
debug_option = click.option(
    "--debug", is_flag=True, help='DEPRECATED - use --log-level=DEBUG as a parameter to `reckoner` instead. May be used with or without `--dry-run`. Or, pass `--debug` to --helm-args')


@click.group(invoke_without_command=True)
@click.version_option(__version__)
@log_level_option
@click.pass_context
def cli(ctx, log_level, *args, **kwargs):
    coloredlogs.install(level=log_level)
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(1)
    pass


@cli.command()
@click.pass_context
@course_file_argument
@dry_run_option
@debug_option
@run_all_option
@only_option
@helm_args_option
@continue_on_error_option
@create_namespace_option
@log_level_option
@update_repos_option
def plot(ctx, run_all, log_level, course_file=None, dry_run=False, debug=False, only=None, helm_args=None, continue_on_error=False, create_namespace=True, update_repos=True):
    """ Install charts with given arguments as listed in yaml file argument """
    coloredlogs.install(level=log_level)
    Config().update_repos = update_repos
    if not run_all:
        if len(only) < 1:
            logging.error("You must pass either --run-all or --only.")
            ctx.exit(1)
    try:
        # Check Schema of Course FileA
        with open(course_file.name, 'rb') as course_file_stream:
            validate_course_file(course_file_stream)
        # Load Reckoner
        r = Reckoner(course_file=course_file, dryrun=dry_run, debug=debug, helm_args=helm_args,
                     continue_on_error=continue_on_error, create_namespace=create_namespace)
        # Convert tuple to list
        only = list(only)
        r.install(only)
    except exception.ReckonerException as err:
        click.echo(click.style("⛵🔥 Encountered errors while reading course file ⛵🔥", fg="bright_red"))
        click.echo(click.style("{}".format(err), fg="red"))
        logging.debug(traceback.format_exc())
        ctx.exit(1)
    except Exception as err:
        # This handles exceptions cleanly, no expected stack traces from reckoner code
        click.echo(click.style("⛵🔥 Encountered unexpected error in Reckoner! Run with DEBUG log level to see details, for example:\n\nreckoner --log-level=DEBUG plot course.yml -o <heading> --dry-run\n\n(or without heading if running the full chart). ⛵🔥", fg="bright_red"))
        if 'log_level' in ctx.parent.params and ctx.parent.params['log_level'].lower() in ['debug', 'trace']:
            click.echo(click.style("{}".format(err), fg='bright_red'))
        logging.debug(traceback.format_exc())
        ctx.exit(1)
    if r.results.has_errors:
        click.echo(click.style("⛵🔥 Encountered errors while running the course ⛵🔥", fg="bright_red"))
        for result in r.results.results_with_errors:
            click.echo(click.style("\n* * * * *\n", fg="bright_red"))
            click.echo(click.style(str(result), fg="bright_red"))
        ctx.exit(1)


@cli.command()
@click.pass_context
@course_file_argument
@run_all_option
@only_option
@helm_args_option
@log_level_option
@update_repos_option
def template(ctx, only, run_all, log_level, course_file=None, helm_args=None, dry_run=False, update_repos=True):
    """Output the template of the chart or charts as they would be installed or upgraded"""

    coloredlogs.install(level=log_level)
    if not run_all:
        if len(only) < 1:
            logging.error("You must pass either --run-all or --only.")
            ctx.exit(1)
    Config().update_repos = update_repos
    try:
        # Check Schema of Course File
        with open(course_file.name, 'rb') as course_file_stream:
            validate_course_file(course_file_stream)
        # Load Reckoner
        r = Reckoner(course_file=course_file, helm_args=helm_args)
        # Convert tuple to list
        only = list(only)
        logging.debug(f'Only templating the following charts: {only}')
        template_results = r.template(only)
        for result in template_results:
            if result.response is not None:
                print(result.response.stdout)
    except exception.ReckonerException as err:
        click.echo(click.style("⛵🔥 Encountered errors while reading course file ⛵🔥", fg="bright_red"))
        click.echo(click.style("{}".format(err), fg="red"))
        logging.debug(traceback.format_exc())
        ctx.exit(1)
    except Exception as err:
        # This handles exceptions cleanly, no expected stack traces from reckoner code
        click.echo(click.style("⛵🔥 Encountered unexpected error in Reckoner! Run with DEBUG log level to see details, for example:\n\nreckoner --log-level=DEBUG plot course.yml -o <heading> --dry-run\n\n(or without heading if running the full chart). ⛵🔥", fg="bright_red"))
        if 'log_level' in ctx.parent.params and ctx.parent.params['log_level'].lower() in ['debug', 'trace']:
            click.echo(click.style("{}".format(err), fg='bright_red'))
        logging.debug(traceback.format_exc())
        ctx.exit(1)
    if r.results.has_errors:
        click.echo(click.style("⛵🔥 Encountered errors while running the course ⛵🔥", fg="bright_red"))
        for result in r.results.results_with_errors:
            click.echo(click.style("\n* * * * *\n", fg="bright_red"))
            click.echo(click.style(str(result), fg="bright_red"))
        ctx.exit(1)


@cli.command()
@click.pass_context
@course_file_argument
@run_all_option
@only_option
@helm_args_option
@log_level_option
@update_repos_option
def get_manifests(ctx, only, run_all, log_level, course_file=None, helm_args=None, update_repos=True):
    """Output the manifests of the chart or charts as they are installed"""

    coloredlogs.install(level=log_level)
    if not run_all:
        if len(only) < 1:
            logging.error("You must pass either --run-all or --only.")
            ctx.exit(1)
    Config().update_repos = update_repos

    try:
        # Check Schema of Course File
        with open(course_file.name, 'rb') as course_file_stream:
            validate_course_file(course_file_stream)
        # Load Reckoner
        r = Reckoner(course_file=course_file, helm_args=helm_args)
        # Convert tuple to list
        only = list(only)
        logging.debug(f'Only getting manifests for the following charts: {only}')
        manifests_results = r.get_manifests(only)
        for result in manifests_results:
            print(result.response.stdout)
    except exception.ReckonerException as err:
        click.echo(click.style("⛵🔥 Encountered errors while reading course file ⛵🔥", fg="bright_red"))
        click.echo(click.style("{}".format(err), fg="red"))
        logging.debug(traceback.format_exc())
        ctx.exit(1)
    except Exception as err:
        # This handles exceptions cleanly, no expected stack traces from reckoner code
        click.echo(click.style("⛵🔥 Encountered unexpected error in Reckoner! Run with DEBUG log level to see details, for example:\n\nreckoner --log-level=DEBUG plot course.yml -o <heading> --dry-run\n\n(or without heading if running the full chart). ⛵🔥", fg="bright_red"))
        if 'log_level' in ctx.parent.params and ctx.parent.params['log_level'].lower() in ['debug', 'trace']:
            click.echo(click.style("{}".format(err), fg='bright_red'))
        logging.debug(traceback.format_exc())
        ctx.exit(1)
    if r.results.has_errors:
        click.echo(click.style("⛵🔥 Encountered errors while running the course ⛵🔥", fg="bright_red"))
        for result in r.results.results_with_errors:
            click.echo(click.style("\n* * * * *\n", fg="bright_red"))
            click.echo(click.style(str(result), fg="bright_red"))
        ctx.exit(1)


@cli.command()
@click.pass_context
@course_file_argument
@run_all_option
@only_option
@helm_args_option
@log_level_option
@update_repos_option
def diff(ctx, only, run_all, log_level, course_file=None, helm_args=None, update_repos=True):
    """Output diff of the templates that would be installed and the manifests that are currently installed"""

    coloredlogs.install(level=log_level)
    if not run_all:
        if len(only) < 1:
            logging.error("You must pass either --run-all or --only.")
            ctx.exit(1)

    Config().update_repos = update_repos
    try:
        # Check Schema of Course FileA
        with open(course_file.name, 'rb') as course_file_stream:
            validate_course_file(course_file_stream)

        # Load Reckoner
        r = Reckoner(course_file=course_file, helm_args=helm_args)
        # Convert tuple to list
        only = list(only)
        logging.debug(f'Only diffing the following charts: {only}')
        diff_results = r.diff(only)
        for result in diff_results:
            print(result.response)
    except exception.ReckonerException as err:
        click.echo(click.style("⛵🔥 Encountered errors while reading course file ⛵🔥", fg="bright_red"))
        click.echo(click.style("{}".format(err), fg="red"))
        logging.debug(traceback.format_exc())
        ctx.exit(1)
    except Exception as err:
        # This handles exceptions cleanly, no expected stack traces from reckoner code
        click.echo(click.style("⛵🔥 Encountered unexpected error in Reckoner! Run with DEBUG log level to see details, for example:\n\nreckoner --log-level=DEBUG plot course.yml -o <heading> --dry-run\n\n(or without heading if running the full chart). ⛵🔥", fg="bright_red"))
        if 'log_level' in ctx.parent.params and ctx.parent.params['log_level'].lower() in ['debug', 'trace']:
            click.echo(click.style("{}".format(err), fg='bright_red'))
        logging.debug(traceback.format_exc())
        ctx.exit(1)
    if r.results.has_errors:
        click.echo(click.style("⛵🔥 Encountered errors while running the course ⛵🔥", fg="bright_red"))
        for result in r.results.results_with_errors:
            click.echo(click.style("\n* * * * *\n", fg="bright_red"))
            click.echo(click.style(str(result), fg="bright_red"))
        ctx.exit(1)


@cli.command()
@click.pass_context
@course_file_argument
@debug_option
@run_all_option
@only_option
@helm_args_option
@continue_on_error_option
@create_namespace_option
@log_level_option
@update_repos_option
def update(ctx, run_all, log_level, course_file=None, dry_run=False, debug=False, only=None, helm_args=None, continue_on_error=False, create_namespace=True, update_repos=True):
    """Checks to see if any thing will have changed, if so, updated the release, if not, does nothing"""
    coloredlogs.install(level=log_level)
    Config().update_repos = update_repos
    if not run_all:
        if len(only) < 1:
            logging.error("You must pass either --run-all or --only.")
            ctx.exit(1)
    try:
        # Check Schema of Course FileA
        with open(course_file.name, 'rb') as course_file_stream:
            validate_course_file(course_file_stream)
        # Load Reckoner
        r = Reckoner(course_file=course_file, debug=debug, helm_args=helm_args,
                     continue_on_error=continue_on_error, create_namespace=create_namespace)
        # Convert tuple to list
        only = list(only)
        r.update(only)
    except exception.ReckonerException as err:
        click.echo(click.style("⛵🔥 Encountered errors while reading course file ⛵🔥", fg="bright_red"))
        click.echo(click.style("{}".format(err), fg="red"))
        logging.debug(traceback.format_exc())
        ctx.exit(1)
    except Exception as err:
        # This handles exceptions cleanly, no expected stack traces from reckoner code
        click.echo(click.style("⛵🔥 Encountered unexpected error in Reckoner! Run with DEBUG log level to see details, for example:\n\nreckoner --log-level=DEBUG plot course.yml -o <heading> --dry-run\n\n(or without heading if running the full chart). ⛵🔥", fg="bright_red"))
        if 'log_level' in ctx.parent.params and ctx.parent.params['log_level'].lower() in ['debug', 'trace']:
            click.echo(click.style("{}".format(err), fg='bright_red'))
        logging.debug(traceback.format_exc())
        ctx.exit(1)
    if r.results.has_errors:
        click.echo(click.style("⛵🔥 Encountered errors while running the course ⛵🔥", fg="bright_red"))
        for result in r.results.results_with_errors:
            click.echo(click.style("\n* * * * *\n", fg="bright_red"))
            click.echo(click.style(str(result), fg="bright_red"))
        ctx.exit(1)


@cli.command()
@click.pass_context
@log_level_option
@course_file_argument
def lint(ctx, log_level, course_file=None):
    """ Validate the course file schema """
    coloredlogs.install(level=log_level)
    try:
        with open(course_file.name, 'rb') as course_file_stream:
            validate_course_file(course_file_stream)
    except exception.ReckonerException as err:
        click.echo(click.style("{}".format(err), fg="red"))
        ctx.exit(1)
    click.echo(click.style("No schema validation errors found.", fg="green"))


@cli.command(name='import')  # import is special word in python, need to rename command here
@click.pass_context
@log_level_option
@click.option("--release_name", help='The release name to import', required=True)
@click.option("--namespace", help='The namespace of the release being imported', required=True)
@click.option("--repository", help='The repository of the chart being imported', required=True)
def import_release(ctx, log_level, release_name, namespace, repository):
    """Outputs a release block that can be used to import the specified release"""
    coloredlogs.install(level=log_level)
    logging.warn("Import is experimental and may be unreliable. Double check all output.")
    release = draft_release(release_name, namespace, repository)
    # Indenting by one to enable redirection of output
    for line in yaml.dump(release).split('\n'):
        print(f"  {line}")


@cli.command()
def version():
    """ Takes no arguments, outputs version info"""
    print(__version__)
