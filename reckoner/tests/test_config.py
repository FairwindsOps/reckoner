import unittest
from reckoner.config import Config


class TestConfig(unittest.TestCase):
    def test_course_base_dir_never_empty(self):
        config = Config()
        config.course_path = 'course.yaml'
        self.assertNotEqual('', config.course_base_directory,
                            "course_base_path has to be None or a real path "
                            "(including '.') because of how it is used in "
                            "Popen. Cannot be an empty string.")
        self.assertIsNone(config.course_base_directory)

        config.course_path = '/some/full/path/course.yml'
        self.assertEqual('/some/full/path', config.course_base_directory)

        config.course_path = './course.yaml'
        self.assertEqual('.', config.course_base_directory)

        config.course_path = '../../relative/course.yml'
        self.assertEqual('../../relative', config.course_base_directory)
