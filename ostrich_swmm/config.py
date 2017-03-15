"""Handle loading of OSTRICH-SWMM config files."""

from __future__ import print_function

import json
import os

import jsonschema
import pkg_resources

config_schema = None
"""The JSON Schema used to validate config files."""


class ConfigException(Exception):
    """A problem with an OSTRICH-SWMM config file."""

    def __init__(self, msg, key=None):
        """Constructor."""
        msg_prefix = 'Configuration invalid'
        if key is not None:
            msg_prefix = '{0}: {1}'.format(msg_prefix, key)
        self.msg = '{0}: {1}'.format(msg_prefix, msg)
        self.key = key


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

    This function will perform some minor setup tasks (such as creating folders
    to store extraction output) in order to catch configuration errors before
    the main work occurs.

    Args:
        config (dict): The configuration to validate.

    Raises:
        ConfigException: The configuration is not valid.
    """
    # If not loaded, load the JSON Schema for config files.
    global config_schema
    if config_schema is None:
        config_schema_path = pkg_resources.resource_filename(
            __name__,
            os.path.join(
                'data',
                'schemas',
                'config.schema.json',
            ),
        )
        with open(config_schema_path) as config_schema_file:
            config_schema = json.load(config_schema_file)

    # Use JSON Schema to validate the config.
    try:
        jsonschema.validate(config, config_schema)
    except jsonschema.ValidationError as e:
        raise ConfigException(e.message)

    # Perform validation steps that cannot be handled through JSON Schema.
    if 'binary_output_path' in config:
        binary_output_path = config['binary_output_path']
        if not os.path.isfile(binary_output_path):
            raise ConfigException(
                '"{0}" is not a SWMM binary output file.'.format(
                    binary_output_path
                ),
                'binary_output_path',
            )
    if 'summary_dir' in config:
        if config['summary_dir'] == '':
            config['summary_dir'] = os.curdir
        summary_dir = config['summary_dir']
        if not os.path.isdir(summary_dir):
            try:
                os.makedirs(summary_dir)
            except OSError:
                raise ConfigException(
                    'Could not create summary directory "{0}"'.format(
                        summary_dir
                    )
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
