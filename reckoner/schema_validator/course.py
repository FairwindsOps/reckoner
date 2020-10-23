import logging
from jsonschema.validators import Draft7Validator as _validator
from io import BufferedReader
from reckoner.yaml.handler import Handler
from reckoner.exception import SchemaValidationError, ReckonerConfigException
from json import loads as read_json_string
from pkgutil import get_data

main_schema = read_json_string(get_data('reckoner', 'assets/course.schema.json'))


class Validator(object):
    def __init__(self, validator=_validator):
        self.validator = validator
        self.errors = []
        self.raw_errors = []

    def check(self, document: dict) -> bool:
        self.errors = []
        v = self.validator(main_schema)
        for err in sorted(v.iter_errors(document), key=lambda e: e.path):
            if 'x-custom-error-message' in err.schema:
                self.errors.append(
                    "(Err: {}) {}".format(
                        err.schema['x-custom-error-message'],
                        err.message,
                    )
                )
            else:
                self.errors.append(err.message)
            self.raw_errors.append(err)

        return len(self.errors) == 0

    @property
    def errors(self):
        return self.__errors

    @errors.setter
    def errors(self, val: list):
        self.__errors = val

    @property
    def raw_errors(self):
        return self.__raw_errors

    @raw_errors.setter
    def raw_errors(self, val: list):
        self.__raw_errors = val


def validate_course_file(course_file: BufferedReader):
    v = Validator()
    course_file_object = Handler.load(course_file)
    v.check(course_file_object)
    if len(v.errors) > 0:
        logging.debug("Schema Validation Errors:")
        for err in v.raw_errors:
            logging.debug("{}".format(err))
        raise SchemaValidationError(
            "Course file has schema validation errors. "
            "Please see the docs on schema validation or --log-level debug for in depth validation output.\n\n{}.".format('\n'.join(v.errors))
        )

def lint_course_file(course_file: BufferedReader):
    v = Validator()
    course_file_object = Handler.load(course_file)
    v.check(course_file_object)
    if len(v.errors) > 0:
        logging.error("Schema Validation Errors:")
        for err in v.raw_errors:
            logging.error("{}".format(err))
        raise SchemaValidationError(
            "Course file has schema validation errors."
        )
