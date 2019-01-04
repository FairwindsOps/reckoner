from reckoner.helm.cmd_response import HelmCmdResponse


class TestHelmCmdResponse(object):
    def test_succeeded_method(self):
        assert HelmCmdResponse(0, None, None, None).succeeded == True
        assert HelmCmdResponse(1, None, None, None).succeeded == False

    def test_properties(self):
        resp = HelmCmdResponse(0, '', '', '')
        for attr in ['exit_code', 'stdout', 'stderr', 'command']:
            assert getattr(resp, attr) != None
