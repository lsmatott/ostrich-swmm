"""A script for connecting OSTRICH with SWMM."""

from __future__ import print_function

import argparse
import os
import sys

from . import config as cfg
from . import inject
from . import extract
from . import run
from .version import __version__


class UsageException(Exception):
    """Raised if script is invoked incorrectly."""

    def __init__(self, msg):
        """Contructor."""
        self.msg = msg


def load_config_with_args(args):
    """Load a configuration file from command-line arguments.

    This function will also apply relevant command-line arguments to the
    generated configuration. For example, if the path to the SWMM binary
    output is specified as an argument, it will replace that value in the
    configuration file.

    Args:
        args (dict): Command-line arguments to apply.

    Returns:
        dict: The configuration options for the program.

    Raises:
        ConfigException: The configuration could not be validated.
        IOError: The config file was not found or was not readable.
        UsageException: The configuration file was not found.
        ValueError: The config file was not valid JSON.
    """
    config_path = args['config']
    if not os.path.isfile(config_path):
        raise UsageException((
            "Config file not found at \"{0}\". "
            "Please create a config file there or "
            "specify a config file elsewhere."
        ).format(config_path))

    config = cfg.load_config(config_path, False)

    if args.get('binary_output_path') is not None:
        config['binary_output_path'] = args['binary_output_path']
    if args.get('summary_dir') is not None:
        config['summary_dir'] = args['summary_dir']
    if args.get('output') is not None:
        config['input_path'] = args['output']
    if args.get('input_template') is not None:
        config['input_template_path'] = args['input_template']
    if args.get('parameters_file') is not None:
        config['input_parameters_path'] = args['parameters_file']

    cfg.validate_config(config)

    return config


def extract_cmd(config):
    """Extract data from a SWMM binary output file.

    Args:
        config (dict): The configuration to use.

    Returns:
        int: An exit code for the script.

    Raises:
        ConfigException: The configuration was invalid.
    """
    extract.perform_extraction_steps(config)

    return 0


def inject_cmd(config):
    """Inject OSTRICH parameters into SWMM input before a run.

    Args:
        config (dict): The configuration to use.

    Returns:
        int: An exit code for the script.

    Raises:
        ConfigException: The configuration was invalid.
    """
    inject.perform_injection(config)

    return 0


def run_cmd(config):
    """Run SWMM with pre- and post-processing steps.

    Args:
        config (dict): The configuration to use.

    Returns:
        int: An exit code for the script.

    Raises:
        ConfigException: The configuration was invalid.
    """
    run.perform_run(config)

    return 0


def main(argv=None):
    """Execute functions of this package as a script.

    Args:
        argv: The list of arguments to use. Defaults to sys.argv.

    Returns:
        int: An exit code for the script.
    """
    if argv is None:
        argv = sys.argv

    try:
        # Set up parsing for main command arguments.
        parser = argparse.ArgumentParser(
            description='A script for connecting OSTRICH with SWMM.',
        )
        parser.add_argument(
            '-v',
            '--version',
            action='version',
            version=__version__,
        )

        # Set up parsing of sub-commands.
        subparsers = parser.add_subparsers(
            title='sub-commands',
            dest='subcommand'
        )

        # Create a parent parser for sub-commands using a config file.
        config_parser = argparse.ArgumentParser(add_help=False)
        config_parser.add_argument(
            '-c',
            '--config',
            default='ostrich-swmm-config.json',
            help='A config file to use.',
        )

        # Create a parent parser for subcommands using SWMM binary output files
        swmm_binary_output_parser = argparse.ArgumentParser(add_help=False)
        swmm_binary_output_parser.add_argument(
            'binary_output_path',
            nargs='?',
            default=None,
            help='The SWMM binary output file to extract data from.',
        )

        # Create a parent parser for subcommands using SWMM summary files
        swmm_summary_parser = argparse.ArgumentParser(add_help=False)
        swmm_summary_parser.add_argument(
            'summary_dir',
            nargs='?',
            default=None,
            help='The directory for SWMM summary data.',
        )

        # Create a parent parser for subcommands using SWMM input templates.
        swmm_input_template_parser = argparse.ArgumentParser(add_help=False)
        swmm_input_template_parser.add_argument(
            '-i',
            '--input-template',
            default=None,
            help='The input file template to use for a SWMM run.',
        )

        # Create a parent parser for subcommands using OSTRICH parameter files.
        ostrich_parameters_parser = argparse.ArgumentParser(add_help=False)
        ostrich_parameters_parser.add_argument(
            '-p',
            '--parameters-file',
            default=None,
            help='The file containing parameters set by OSTRICH.',
        )

        # Create a parent parser for subcommands creating new SWMM input files.
        new_swmm_input_parser = argparse.ArgumentParser(add_help=False)
        new_swmm_input_parser.add_argument(
            '-o',
            '--output',
            default=None,
            help='The path to store a new SWMM input file.',
        )

        # Set up parsing for the extraction sub-command.
        subparsers.add_parser(
            'extract',
            help='Extract data from a SWMM binary output file.',
            parents=[
                config_parser,
                swmm_binary_output_parser,
                swmm_summary_parser,
            ],
        )

        # Set up parsing for the injection sub-command.
        subparsers.add_parser(
            'inject',
            help='Inject OSTRICH parameters into SWMM input before a run.',
            parents=[
                config_parser,
                ostrich_parameters_parser,
                swmm_input_template_parser,
                new_swmm_input_parser,
            ],
        )

        # Set up parsing for the run sub-command.
        subparsers.add_parser(
            'run',
            help='Run SWMM with pre- and post-processing steps.',
            parents=[
                config_parser,
            ],
        )

        # Parse arguments.
        args = vars(parser.parse_args(argv[1:]))
        config = load_config_with_args(args)

        # Call selected subcommand.
        subcommands = {
            'extract': extract_cmd,
            'inject': inject_cmd,
            'run': run_cmd,
        }
        return subcommands[args['subcommand']](config)
    except (UsageException, cfg.ConfigException) as e:
        print(e.msg, file=sys.stderr)
        print('For help, use --help or [sub-command] --help.', file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
