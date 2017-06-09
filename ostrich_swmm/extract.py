"""Functionality for extracting data from SWMM output."""

import csv

import numpy as np
import os
import swmmtoolbox.swmmtoolbox as swmmtoolbox

from . import config as cfg


def perform_node_extraction(
    binary_output,
    node_output_file,
    node_names,
    statistics,
    event_threshold_flow_rate=0,
):
    """Perform extraction of node data from a binary output file.

    Args:
        binary_output (swmmtoolbox.SwmmExtract): The output to extract from.
        node_output_file (file): The file to output extracted data to.
        node_names (Iterable): A list of node names to extract data for.
        statistics (Iterable): A list of statistics to extract.
        event_threshold_flow_rate (Number): The flow rate above which a node
            is considered to have flow. Defaults to 0.
    """
    # Get the indicies of the relevant data in the binary output.
    node_type = binary_output.TypeCheck('node')
    node_total_inflow_variable_index = next(
        index
        for index, name
        in binary_output.varcode[node_type].items()
        if name == 'Total_inflow'
    )

    # Set up arrays to hold calculations for nodes.
    num_nodes = len(node_names)
    nodes_flow_previously_active = np.zeros(num_nodes, np.bool_)
    nodes_flow_active_intervals = np.zeros(num_nodes, np.uint64)
    nodes_total_flow_events = np.zeros(num_nodes, np.uint64)
    nodes_total_flow_rate_sums = np.zeros(num_nodes, np.float64)

    # For each period recorded in the output, extract and calculate data.
    report_interval_seconds = binary_output.reportinterval.total_seconds()
    nodes_current_values = np.zeros(num_nodes, np.float64)
    for period in range(binary_output.nperiods):
        for node_index, node_name in enumerate(node_names):
            swmm_timestamp, value = binary_output.GetSwmmResults(
                node_type,
                node_name,
                node_total_inflow_variable_index,
                period,
            )
            nodes_current_values[node_index] = value

        nodes_flow_currently_active = (
            nodes_current_values > event_threshold_flow_rate
        )
        nodes_flow_active_intervals[nodes_flow_currently_active] += 1
        nodes_flow_newly_active = np.logical_and(
            nodes_flow_currently_active,
            np.logical_not(nodes_flow_previously_active)
        )
        nodes_total_flow_events[nodes_flow_newly_active] += 1
        nodes_total_flow_rate_sums += nodes_current_values

        nodes_flow_previously_active = nodes_flow_currently_active

    # Calculate post-extraction statistics.
    nodes_total_flow_volumes = (
        nodes_total_flow_rate_sums * report_interval_seconds
    )
    nodes_total_flow_durations = (
        nodes_flow_active_intervals * report_interval_seconds
    )

    # Write the requested statistics out to the given file as CSV.
    csv_writer = csv.writer(node_output_file)
    csv_writer.writerow(statistics)

    csv_columns = []
    node_stat_names_to_columns = {
        'node_name': node_names,
        'num_flow_events': nodes_total_flow_events,
        'total_flow_volume': nodes_total_flow_volumes,
        'total_flow_duration': nodes_total_flow_durations,
    }

    for statistic in statistics:
        csv_columns.append(node_stat_names_to_columns[statistic])

    csv_writer.writerows(zip(*csv_columns))


def perform_extraction_steps(config, validate=True):
    """Perform the extraction steps specified in a configuration.

    Args:
        config: The config to get extraction steps from.
        validate (boolean): Validate the configuration before attempting
            to use it. Defaults to True.

    Raises:
        ConfigException: The configuration is invalid.
    """
    if validate:
        validate_config(config)

    binary_output = swmmtoolbox.SwmmExtract(
        config['binary_output_path']
    )

    for step in config['extract']['steps']:
        # If step has been explicitly disabled, skip it.
        step_enabled = step.get('enabled', True)
        if not step_enabled:
            continue

        if step['type'] == 'node':
            node_output_path = os.path.join(
                config['summary_dir'],
                step['output_path'],
            )
            node_output_file = open(node_output_path, 'wb')

            node_extraction_args = {
                'binary_output': binary_output,
                'node_output_file': node_output_file,
                'node_names': step['nodes'],
                'statistics': step['statistics'],
            }

            if 'event_threshold_flow_rate' in step:
                node_extraction_args['event_threshold_flow_rate'] = (
                    step['event_threshold_flow_rate']
                )

            perform_node_extraction(**node_extraction_args)

            node_output_file.close()


def validate_config(config, perform_file_checks=True):
    """Validate a configuration for use with this functionality.

    Args:
        config (dict): The configuration to validate.
        perform_file_checks (boolean): Check if required files exist.
            Defaults to true.

    Raises:
        ConfigException: The configuration is invalid.
    """
    cfg.validate_required_sections(config, [
        'binary_output_path',
        'summary_dir',
        'extract',
    ], 'extract')

    if perform_file_checks:
        cfg.validate_file_exists(config, 'binary_output_path')
        cfg.validate_dir_exists(config, 'summary_dir')
