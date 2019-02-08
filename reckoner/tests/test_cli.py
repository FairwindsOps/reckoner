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

    def test_supports_loglevel(self):
        """assure we have a global command for --log-level"""
        runner = CliRunner()
        result = runner.invoke(
            cli.cli, args=['--log-level', 'DEBUG', 'version'])

        self.assertEqual(0, result.exit_code)
        self.assertNotEqual('', result.output)

    def test_exits_without_subcommand(self):
        """Assure we fail when run without subcommands and show some info"""
        runner = CliRunner()
        result = runner.invoke(cli.cli)

        self.assertEqual(1, result.exit_code)
        self.assertNotEqual(u'', result.output)

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
