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
        self.assertNotEqual(u'', result.output)


class TestCliPlot(unittest.TestCase):
    @mock.patch('reckoner.cli.Reckoner', autospec=True)
    def test_plot_exists(self, reckoner_mock):
        """Assure we have a plot command and it calls reckoner install"""
        reckoner_instance = reckoner_mock()
        reckoner_instance.install.side_effect = [None]
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('nonexistant.file', 'w') as fake_file:
                fake_file.write('')

            result = runner.invoke(cli.plot, args=['nonexistant.file'])

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
                'file',
            ]
        }

        assert_required_params(required, cli.plot.params)


def assert_required_params(required_options, list_of_cli_params):
    all_params = {}
    for param in list_of_cli_params:
        if param.param_type_name not in all_params.keys():
            all_params[param.param_type_name] = []
        [all_params[param.param_type_name].append(opt) for opt in param.opts]

    for opt_type, opt_type_list in required_options.items():
        assert opt_type in all_params.keys(), "Missing option type '{}' from cli params. Check if an argument or option was removed.".format(opt_type)
        for opt in opt_type_list:
            assert opt in all_params[opt_type], "Option '{}' of type '{}' may be missing. Consider this contract broken and version bumping if you intend to remove the param.".format(
                opt, opt_type)
