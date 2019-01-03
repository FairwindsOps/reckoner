class HelmCmdResponse(object):
    """HelmCmdResponse has the result of the command with the exit_code, stderr and stdout. Also includes the originally run command."""

    def __init__(self, exit_code, stderr, stdout, command):
        self._stderr = stderr
        self._stdout = stdout
        self._exit_code = exit_code
        self._command = command

    @property
    def exit_code(self):
        return self._exit_code

    @property
    def stderr(self):
        return self._stderr

    @property
    def stdout(self):
        return self._stdout

    @property
    def command(self):
        return self._command

    @property
    def succeeded(self):
        return self._exit_code == 0
