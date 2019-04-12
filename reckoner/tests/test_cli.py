# Copyright 2019 ReactiveOps Inc
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

"""Testing of CLI commands in click, contract tests"""

import unittest
import mock
from click.testing import CliRunner
from reckoner import cli


class TestCli(unittest.TestCase):
    """
    Test all the contracts of the command line tool.
    If something changes in here than you should consider that in your version
    bumping scheme.
    """

    def test_version(self):
        """Assure version subcommand exists"""
        runner = CliRunner()
        result = runner.invoke(cli.version)

        self.assertEqual(0, result.exit_code)
        self.assertNotEqual('', result.output)

        result = runner.invoke(cli.cli, args=['--version'])

        self.assertEqual(0, result.exit_code)
        self.assertNotEqual('', result.output)

    def test_group_options(self):
        """
        Assure we have a global command options/flags
        This will ONLY fail if you remove an expected flag, NOT if you add a
        new option!!
        """
        required = {
            'option': [
                '--version',
                '--log-level',
            ]
        }
        assert_required_params(required, cli.cli.params)

    def test_exits_without_subcommand(self):
        """Assure we fail when run without subcommands and show some info"""
        runner = CliRunner()
        result = runner.invoke(cli.cli)

        self.assertEqual(1, result.exit_code)
        self.assertNotEqual('', result.output)


class TestCliPlot(unittest.TestCase):
    @mock.patch('reckoner.cli.Reckoner', autospec=True)
    def test_plot_exists(self, reckoner_mock):
        """Assure we have a plot command and it calls reckoner install"""
        reckoner_instance = reckoner_mock()
        reckoner_instance.install.side_effect = [None]
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('nonexistent.file', 'wb') as fake_file:
                fake_file.write(''.encode())

            result = runner.invoke(cli.plot, args=['nonexistent.file'])

        self.assertEqual(0, result.exit_code, result.output)
        reckoner_instance.install.assert_called_once()

    def test_plot_options(self):
        required = {
            'option': [
                '--dry-run',
                '--debug',
                '--helm-args',
                '--heading',
                '--only',
                '--local-development',
            ],
            'argument': [
                'course_file',
            ]
        }

        assert_required_params(required, cli.plot.params)


def assert_required_params(required_options, list_of_cli_params):
    all_params = {}
    for param in list_of_cli_params:
        if param.param_type_name not in list(all_params.keys()):
            all_params[param.param_type_name] = []
        [all_params[param.param_type_name].append(opt) for opt in param.opts]

    for opt_type, opt_type_list in list(required_options.items()):
        assert opt_type in list(all_params.keys()), "Missing option type '{}' from cli params. Check if an argument or option was removed.".format(opt_type)
        for opt in opt_type_list:
            assert opt in all_params[opt_type], "Option '{}' of type '{}' may be missing. Consider this contract broken and version bumping if you intend to remove the param.".format(
                opt, opt_type)
