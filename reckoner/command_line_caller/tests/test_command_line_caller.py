import unittest
from reckoner.command_line_caller import Response


class TestResponse(unittest.TestCase):
    def test_properties(self):
        required_attrs = {
            'stdout': 'stdout value',
            'stderr': 'stderr value',
            'exitcode': 0,
            'command_string': 'command -that -ran',
        }
        response = Response(**required_attrs)
        for attr, value in required_attrs.items():
            self.assertEqual(getattr(response, attr), value)

    def test_bool(self):
        response = Response('', '', 127, '')
        self.assertFalse(response, "Any response where exitcode is not 0 should return false")

        response = Response('', '', 0, '')
        self.assertTrue(response, "All responses with exitcode 0 should return True")
