import unittest
from reckoner import cli
from click.testing import CliRunner


class TestCli(unittest.TestCase):
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli.version)

        self.assertEqual(0, result.exit_code)
        self.assertNotEqual('', result.output)

        result = runner.invoke(cli.cli, args=['--version'])

        self.assertEqual(0, result.exit_code)
        self.assertNotEqual('', result.output)

    def test_supports_loglevel(self):
        runner = CliRunner()
        result = runner.invoke(cli.cli, args=['--log-level', 'DEBUG', 'version'])

        self.assertEqual(0, result.exit_code)
        self.assertNotEqual('', result.output)

    def test_exits_without_subcmd(self):
        runner = CliRunner()
        result = runner.invoke(cli.cli)

        self.assertEqual(1, result.exit_code)
        self.assertNotEqual(u'', result.output)
