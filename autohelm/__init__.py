
import subprocess


class AutoHelmSubprocess(object):

    @classmethod
    def check_call(cls, *args, **kwargs):
        return subprocess.check_call(*args, **kwargs)

    @classmethod
    def check_output(cls, *args, **kwargs):
        return subprocess.check_output(*args, **kwargs)

    @classmethod
    def call(cls, *args, **kwargs):
        return subprocess.call(*args, **kwargs)
