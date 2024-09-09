"""Functionality for running SWMM with pre- and post-processing steps."""

import subprocess

import sys

if len(sys.argv) > 1 and sys.argv[1] == "run_debug" :
    debug_mode = True
else :
    debug_mode = False

if debug_mode == True :
    # use these imports when debugging using vs code
    import config as cfg
    import extract
    import inject
else :
    # these imports don't work when debugging using vs code
    from . import config as cfg
    from . import extract
    from . import inject

def perform_run(config, validate=True):
    """Perform a run as specified by a configuration.

    Args:
        config: The config to get run information from.
        validate (boolean): Validate the configuration before attempting
            to use it. Defaults to True.

    Raises:
        ConfigException: The configuration is invalid.
    """
    if validate:
        validate_config(config)

    inject.perform_injection(config, validate=False)

    input_path = config['input_path']
    binary_output_path = config['binary_output_path']
    report_output_path = config.get('report_output_path')
    if report_output_path is None:
        if binary_output_path.endswith('.out'):
            report_base_path = binary_output_path[:-4]
        else:
            report_base_path = binary_output_path
        report_output_path = '{0}.rpt'.format(report_base_path)

    subprocess.call([
        config['swmm_path'],
        input_path,
        report_output_path,
        binary_output_path,
    ])

    extract.perform_extraction_steps(config, validate=False)


def validate_config(config):
    """Validate a configuration for use with this functionality.

    Args:
        config (dict): The configuration to validate.

    Raises:
        ConfigException: The configuration is invalid.
    """
    cfg.validate_required_sections(config, [
        'binary_output_path',
        'input_path',
        'swmm_path',
    ], 'run')
    cfg.validate_executable_path(config, 'swmm_path')

    # Validate with modules used by this module.
    inject.validate_config(config)
    extract.validate_config(config, perform_file_checks=False)
