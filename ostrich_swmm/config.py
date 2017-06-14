"""Handle loading of OSTRICH-SWMM config files."""

from __future__ import print_function

import distutils.spawn
import json
import os

import jsonschema
import pkg_resources

config_schema_path = None
"""The path to the JSON Schema used to validate config files."""

json_schema_cache = {}
"""A cache of JSON Schemas read from file paths."""


class ConfigException(Exception):
    """A problem with an OSTRICH-SWMM config file."""

    def __init__(self, msg, key=None):
        """Constructor."""
        msg_prefix = 'Configuration invalid'
        if key is not None:
            msg_prefix = '{0}: {1}'.format(msg_prefix, key)
        self.msg = '{0}: {1}'.format(msg_prefix, msg)
        self.key = key


def get_package_json_schema_path(filename):
    """Get the path to a JSON Schema file included in this package.

    Args:
        filename (string): The name of the JSON Schema file.

    Returns:
        string: The full path to the JSON Schema file.
    """
    return pkg_resources.resource_filename(
        __name__,
        os.path.join(
            'data',
            'schemas',
            filename,
        ),
    )


def load_config(config_path, validate=True):
    """Load a configuration from a file at a given path.

    Args:
        config_path (str): A path to a config file to load.
        validate (bool, optional): If true, validate the configuration.
            Defaults to True.

    Returns:
        dict: A configuration for the program.

    Raises:
        ConfigException: The configuration could not be validated.
        IOError: The file was not found or was not readable.
        ValueError: The file was not valid JSON.
    """
    with open(config_path) as config_file:
        config = json.load(config_file)

    if validate:
        validate_config(config)

    return config


def validate_config(config):
    """Validate a given configuration.

    Minor tweaks may be made to the configuration as part of this function
    to reduce redundant substitutions elsewhere in the module.

    Args:
        config (dict): The configuration to validate.

    Raises:
        ConfigException: The configuration is not valid.
    """
    # If not loaded, load the JSON Schema for config files.
    global config_schema_path
    if config_schema_path is None:
        config_schema_path = get_package_json_schema_path('config.schema.json')

    # Use JSON Schema to validate the config.
    validate_against_json_schema(config, config_schema_path)

    # Perform validation steps that cannot be handled through JSON Schema.
    if 'summary_dir' in config:
        if config['summary_dir'] == '':
            config['summary_dir'] = os.curdir
    if 'swmm_path' not in config:
        config['swmm_path'] = 'swmm5'


def validate_against_json_schema(o, schema_path):
    """Validate an object against a JSON Schema.

    Args:
        o (mixed): The object to validate.
        schema_path (string): The path to the JSON Schema file to use.

    Raises:
        ConfigException: The object or JSON Schema was invalid.
        IOError: The JSON Schema file could not be opened or read.
    """
    if schema_path not in json_schema_cache:
        with open(schema_path) as schema_file:
            json_schema_cache[schema_path] = json.load(schema_file)

    schema = json_schema_cache[schema_path]
    try:
        jsonschema.validate(o, schema)
    except jsonschema.ValidationError as e:
        raise ConfigException(e.message)


def validate_executable_path(config, section):
    """Validate that a path to an executable is valid.

    Args:
        config (dict): A configuration with an executable path to check.
        section (string): The key to the executable path to check.

    Raises:
        ConfigException: The path was not valid.
    """
    executable_path = config[section]
    if not distutils.spawn.find_executable(executable_path):
        raise ConfigException(
            (
                'Executable "{0}" could not be found in PATH '
                'or on file system.'
            ).format(executable_path),
            section,
        )


def validate_file_exists(config, section):
    """Validate that a file exists.

    Args:
        config (dict): A configuration with a file path to check.
        section (string): The key to the file path in the config to check.

    Raises:
        ConfigException: The file was not found.
    """
    file_path = config[section]
    if not os.path.isfile(file_path):
        raise ConfigException(
            '"{0}" is not a file.'.format(file_path),
            section,
        )


def validate_dir_exists(config, section, create_dir=True, path_is_file=False):
    """Validate that a directory exists and optionally create it.

    Args:
        config (dict): A configuration with a directory path to check.
        section (string): The key to the directory path in the config to check.
        create_dir (bool, optional): Attempt creation of the directory if
            it does not exist. (Defaults to True.)
        path_is_file (bool, optional): If enabled, treats the path as a file's
            path and checks the directory the file would be contained in.
            (Defaults to False.)

    Raises:
        ConfigException: The directory was not found nor created.
    """
    dir_path = config[section]
    if path_is_file:
        dir_path = os.path.dirname(dir_path)
        if dir_path == '':
            dir_path = os.curdir
    if not os.path.isdir(dir_path):
        if not create_dir:
            raise ConfigException(
                '"{0}" is not a directory.'.format(
                    dir_path
                ),
                section,
            )

        try:
            os.makedirs(dir_path)
        except OSError:
            raise ConfigException(
                'Could not create directory "{0}".'.format(
                    dir_path
                ),
                section,
            )


def validate_required_sections(config, sections, dependent):
    """Validate that the given sections are present in the config.

    Args:
        config (dict): A configuration to validate.
        sections (Iterable): The sections of the config that are required.
        dependent (string): The functionality requiring the sections.

    Raises:
        ConfigException: A required section was missing from the config.
    """
    for section in sections:
        if section not in config:
            raise ConfigException(
                'Missing required section for {0}: "{1}"'.format(
                    dependent,
                    section,
                )
            )
