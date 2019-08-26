import logging
from jsonschema.validators import Draft7Validator as _validator
from io import BufferedReader
from reckoner.yaml.handler import Handler
from reckoner.exception import SchemaValidationError

main_schema = {
    'definitions': {
        'repository': {
            'type': 'object',
            'properties': {
                'url': {'type': 'string'},
                'path': {'type': 'string'},
                'git': {'type': 'string'},
                'name': {'type': 'string'},
            },
        },
        'hooks': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'post_install': {
                    'oneOf': [
                        {'type': 'array'},
                        {'type': 'string'},
                    ]
                },
                'pre_install': {
                    'oneOf': [
                        {'type': 'array'},
                        {'type': 'string'},
                    ]
                },
            },
        },
        'chart': {
            'type': 'object',
            'propertyNames': {
                'pattern': '^[a-zA-Z0-9_-]{1,63}$',
                'custom_error_message': 'Chart release names must be alphanumeric with "_" and "-" and be between 1 and 63 characters',
            },
            'additionalProperties': False,
            'patternProperties': {
                '^.+$': {
                    'type': 'object',
                    'additionalProperties': False,
                    'properties': {
                        'namespace': {'type': 'string'},
                        'chart': {'type': 'string'},
                        'repository': {
                            'oneOf': [
                                {'type': 'string'},
                                {'$ref': '#definitions/repository'},
                            ],
                            'custom_error_message': 'Problem Parsing Repositories Schema; expecting string or map',
                        },
                        'version': {'type': 'string'},
                        'hooks': {
                            '$ref': '#definitions/hooks',
                        },
                        'plugins': {'type': 'string'},
                        'files': {
                            'type': 'array',
                            'items': {
                                'type': 'string',
                            }
                        },
                        'values': {'type': 'object'},
                        'set-values': {'type': 'object'},
                        'values-strings': {'type': 'object'},
                    },
                    'custom_error_message': 'Problem Parsing Chart Schema',
                }
            },
        }
    },
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'namespace': {'type': 'string'},
        'charts': {'$ref': '#/definitions/chart'},
        'minimum_versions': {
            'type': 'object',
        },
        'repositories': {
            'type': 'object',
            'patternProperties': {
                '^.*$': {
                    '$ref': '#definitions/repository'
                },
            },
        },
        'repository': {'type': 'string'},
        'context': {
            'type': 'string',
        },
        'helm_args': {
            'type': 'array',
            'items': {
                'type': 'string',
            }
        },
    },
    'required': ['namespace', 'charts'],
    'custom_error_message': 'Problem found in root of course'
}


class Validator(object):
    def __init__(self, validator=_validator):
        self.validator = validator
        self.errors = []
        self.raw_errors = []

    def check(self, document: dict) -> bool:
        self.errors = []
        v = self.validator(main_schema)
        for err in sorted(v.iter_errors(document), key=lambda e: e.path):
            if 'custom_error_message' in err.schema.keys():
                self.errors.append(
                    "(Err: {}) {}".format(
                        err.schema['custom_error_message'],
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
    v.check(Handler.load(course_file))
    if len(v.errors) > 0:
        logging.debug("Schema Validation Errors:")
        for err in v.raw_errors:
            logging.debug("{}".format(err))
        raise SchemaValidationError(
            "Course file has schema validation errors. "
            "Please see the docs on schema validation or --log-level debug for in depth validation output.\n\n{}.".format('\n'.join(v.errors))
        )
    # reset the read point to the beginning of the file
    course_file.seek(0)
