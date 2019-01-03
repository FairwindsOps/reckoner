class HelmCommand(object):
    """Intended to simplify the contract for the helm provider."""

    def __init__(self, command, arguments=[]):
        self._errors = []
        self.validate_command(command)
        self.validate_arguments(arguments)
        # TODO: Verify if we actually want to raise errors here or handle with logging
        self._raise_validation_errors

        self._command = command
        self._arguments = arguments

    def validate_command(self, cmd):
        if not cmd:
            self._errors.append('Command cannot be empty.')

    def validate_arguments(self, args):
        if not hasattr(args, '__iter'):
            self._errors.append('Arguments must be a list')

    @staticmethod
    def _raise_validation_errors(errors):
        if errors:
            raise Exception("Error checking HelmCommand: {}".format(", ".join(errors)))

    @property
    def command(self):
        return self._command

    @property
    def arguments(self):
        return self._arguments

    def __str__(self):
        return 'helm ' + self._command + ' ' + ' '.join(self._arguments)
