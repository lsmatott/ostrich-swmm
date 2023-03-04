"""Functionality for extracting data from SWMM output."""

import csv
import datetime as dt

import numpy as np
import os
import sys
import platform
import swmmtoolbox.swmmtoolbox as swmmtoolbox

if sys.argv[1] == "run_debug" :
    debug_mode = True
else :
    debug_mode = False

if debug_mode == True :
    # use these imports when debugging using vc code
    SWMM_EPOCH_DATETIME = dt.datetime(1899, 12, 30)
    import config as cfg
else :
    # these imports don't work when debugging using vs code
    from . import SWMM_EPOCH_DATETIME
    from . import config as cfg

def convert_swmm_ts_to_datetime(swmm_ts):
    """Convert a SWMM timestamp to a Python datetime.

    Args:
        swmm_ts: The SWMM timestamp to convert.

    Returns:
        datetime: The datetime equivalent of the SWMM timestamp.
    """
    return SWMM_EPOCH_DATETIME + dt.timedelta(days=swmm_ts)


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
        node_output_file (filename): The file to output extracted data to.
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

    nodes_current_flow_event_start_times = [None] * num_nodes
    nodes_current_flow_event_rate_sums = np.zeros(num_nodes, np.float64)
    nodes_current_flow_event_active_intervals = np.zeros(num_nodes, np.uint64)
    nodes_flow_events = [[] for n in range(num_nodes)]

    # For each period recorded in the output, extract and calculate data.
    previous_time = binary_output.startdate
    report_interval_seconds = binary_output.reportinterval.total_seconds()
    nodes_current_values = np.zeros(num_nodes, np.float64)
    for period in range(binary_output.nperiods):
        # Get this period's values for each node.
        for node_index, node_name in enumerate(node_names):
            swmm_timestamp, value = binary_output.GetSwmmResults(
                node_type,
                node_name,
                node_total_inflow_variable_index,
                period,
            )
            nodes_current_values[node_index] = value

        # Convert this period's SWMM timestamp to a Python datetime.
        current_time = convert_swmm_ts_to_datetime(swmm_timestamp)

        # Determine the activity states for each node.
        nodes_flow_currently_active = (
            nodes_current_values > event_threshold_flow_rate
        )
        nodes_flow_newly_active = np.logical_and(
            nodes_flow_currently_active,
            np.logical_not(nodes_flow_previously_active)
        )
        nodes_flow_newly_inactive = np.logical_and(
            np.logical_not(nodes_flow_currently_active),
            nodes_flow_previously_active
        )

        # Perform calculations involving totals for each node.
        nodes_flow_active_intervals[nodes_flow_currently_active] += 1
        nodes_total_flow_events[nodes_flow_newly_active] += 1
        nodes_total_flow_rate_sums += nodes_current_values

        # Perform calculations involving current events for each node.
        for node_index, newly_inactive in enumerate(nodes_flow_newly_inactive):
            if not newly_inactive:
                continue

            nodes_flow_events[node_index].append({
                'start': nodes_current_flow_event_start_times[node_index],
                'end': previous_time,
                'duration': (
                    nodes_current_flow_event_active_intervals[node_index]
                    * report_interval_seconds
                ),
                'volume': (
                    nodes_current_flow_event_rate_sums[node_index]
                    * report_interval_seconds
                ),
            })
            nodes_current_flow_event_start_times[node_index] = None

        for node_index, newly_active in enumerate(nodes_flow_newly_active):
            if not newly_active:
                continue

            nodes_current_flow_event_start_times[node_index] = previous_time
            nodes_current_flow_event_rate_sums[node_index] = 0
            nodes_current_flow_event_active_intervals[node_index] = 0

        nodes_current_flow_event_active_intervals[
            nodes_flow_currently_active
        ] += 1
        nodes_current_flow_event_rate_sums += nodes_current_values

        # Move values for the next period.
        previous_time = current_time
        nodes_flow_previously_active = nodes_flow_currently_active

    # Cleanup unfinished current events.
    for node_index, active in enumerate(nodes_flow_currently_active):
        if not active:
            continue

        nodes_flow_events[node_index].append({
            'start': nodes_current_flow_event_start_times[node_index],
            'end': current_time,
            'duration': (
                nodes_current_flow_event_active_intervals[node_index]
                * report_interval_seconds
            ),
            'volume': (
                nodes_current_flow_event_rate_sums[node_index]
                * report_interval_seconds
            ),
        })

    # Calculate post-extraction statistics.
    nodes_total_flow_volumes = (
        nodes_total_flow_rate_sums * report_interval_seconds
    )
    nodes_total_flow_durations = (
        nodes_flow_active_intervals * report_interval_seconds
    )

    nodes_notable_events = {
        'first': [
            node_events[0]
            if node_events
            else None
            for node_events
            in nodes_flow_events
        ],
        'last': [
            node_events[-1]
            if node_events
            else None
            for node_events
            in nodes_flow_events
        ],
        'max_volume': [
            max(node_events, key=lambda event: event['volume'])
            if node_events
            else None
            for node_events
            in nodes_flow_events
        ],
        'max_duration': [
            max(node_events, key=lambda event: event['duration'])
            if node_events
            else None
            for node_events
            in nodes_flow_events
        ],
    }
    if sys.version_info[0] == 3:
        nodes_notable_events_start_strings = {
            event_type: [
                event['start'].isoformat()
                if event is not None
                else ''
                for event
                in events
            ]
            for event_type, events
            in nodes_notable_events.items()
        }
        nodes_notable_events_end_strings = {
            event_type: [
                event['end'].isoformat()
                if event is not None
                else ''
                for event
                in events
            ]
            for event_type, events
            in nodes_notable_events.items()
        }
        nodes_notable_events_volumes = {
            event_type: [
                event['volume']
                if event is not None
                else 0
                for event
                in events
            ]
            for event_type, events
            in nodes_notable_events.items()
        } 
        nodes_notable_events_durations = {
            event_type: [
                event['duration']
                if event is not None
                else 0
                for event
                in events
            ]
            for event_type, events
            in nodes_notable_events.items()
        }
    else:
        nodes_notable_events_start_strings = {
            event_type: [
                event['start'].isoformat()
                if event is not None
                else ''
                for event
                in events
            ]
            for event_type, events
            in nodes_notable_events.iteritems()
        }
        nodes_notable_events_end_strings = {
            event_type: [
                event['end'].isoformat()
                if event is not None
                else ''
                for event
                in events
            ]
            for event_type, events
            in nodes_notable_events.iteritems()
        }
        nodes_notable_events_volumes = {
            event_type: [
                event['volume']
                if event is not None
                else 0
                for event
                in events
            ]
            for event_type, events
            in nodes_notable_events.iteritems()
        } 
        nodes_notable_events_durations = {
            event_type: [
                event['duration']
                if event is not None
                else 0
                for event
                in events
            ]
            for event_type, events
            in nodes_notable_events.iteritems()
        }

    # see https://stackoverflow.com/questions/30929363/csv-writerows-puts-newline-after-each-row    
    if platform.system == "Windows" :
        new_line = ''
    else :
        new_line = '\n'
    
    # write out a human readable version of the .csv.
    node_summary_file = node_output_file.replace('.csv', '_summary.txt')
    node_sum = open(node_summary_file, 'w', newline=new_line)

    with open(node_output_file, 'w', newline=new_line) as node_out:
        # Write the requested statistics out to the given file as CSV.
        csv_writer = csv.writer(node_out)
        csv_writer.writerow(statistics)

        csv_columns = []
        node_stat_names_to_columns = {
            'node_name': node_names,
            'num_flow_events': nodes_total_flow_events,
            'total_flow_volume': nodes_total_flow_volumes,
            'total_flow_duration': nodes_total_flow_durations,
            'first_flow_start': nodes_notable_events_start_strings['first'],
            'first_flow_end': nodes_notable_events_end_strings['first'],
            'first_flow_duration': nodes_notable_events_durations['first'],
            'first_flow_volume': nodes_notable_events_volumes['first'],

            'last_flow_start': nodes_notable_events_start_strings['last'],
            'last_flow_end': nodes_notable_events_end_strings['last'],
            'last_flow_duration': nodes_notable_events_durations['last'],
            'last_flow_volume': nodes_notable_events_volumes['last'],

            'max_volume_flow_start': nodes_notable_events_start_strings[
                'max_volume'
            ],
            'max_volume_flow_end': nodes_notable_events_end_strings[
                'max_volume'
            ],
            'max_volume_flow_duration': nodes_notable_events_durations[
                'max_volume'
            ],
            'max_volume_flow_volume': nodes_notable_events_volumes[
                'max_volume'
            ],

            'max_duration_flow_start': nodes_notable_events_start_strings[
                'max_duration'
            ],
            'max_duration_flow_end': nodes_notable_events_end_strings[
                'max_duration'
            ],
            'max_duration_flow_duration': nodes_notable_events_durations[
                'max_duration'
            ],
            'max_duration_flow_volume': nodes_notable_events_volumes[
                'max_duration'
            ],
        }

        stat_names = [];
        for statistic in statistics:
            val = node_stat_names_to_columns[statistic]
            csv_columns.append(val)
            stat_names.append(statistic)
        
        for sc_index in range(0,len(csv_columns[0])):
            for stat_index in range(0, len(csv_columns)):
                stat_name = stat_names[stat_index]
                stat_value = csv_columns[stat_index][sc_index]
                if stat_name == 'node_name' :
                    ident = ''
                else :
                    ident = '   '
                node_sum.write(ident + stat_name + ' : ' + str(stat_value) + '\n')
            node_sum.write('='*40 + '\n')
        csv_writer.writerows(zip(*csv_columns))
    node_sum.close()

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

    try:
         binary_output = swmmtoolbox.SwmmExtract(
            config['binary_output_path'])
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
    
                node_extraction_args = {
                    'binary_output': binary_output,
                    'node_output_file': node_output_path,
                    'node_names': step['nodes'],
                    'statistics': step['statistics'],
                }
                outname_stats=step['output_path']
                if 'lid_selection' in config :
                   outname_lids=config['lid_selection']
                else :
                    outname_lids = ''
    
                if 'event_threshold_flow_rate' in step:
                    node_extraction_args['event_threshold_flow_rate'] = (
                        step['event_threshold_flow_rate']
                    )
    
                perform_node_extraction(**node_extraction_args)
                if 'results_path' not in config:
                    config[ 'results_path' ] = node_output_path
                perform_append(config, outname_stats, outname_lids)
    
    except Exception as error: # catch *all* exceptions
        print(error)

        print("Creating expected output using arbitrairly large numbers.")
        
        #build the path to copy the output used for infeasible solutions
        inf_out_path = cfg.get_package_json_schema_path('infeasible_config_out')
        
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
        
         
         #copy the infeasible solutions output
        with open(node_output_path,'a') as outfile:
            with open(inf_out_path) as infile:
                for line in infile:
                    outfile.write(line)
            
def perform_append(config, outname_stats, outname_lids, validate=True):
    #read model results from swmm and number of lids
    outname_stats = os.path.join( config['summary_dir'], outname_stats )
    filenames = [outname_stats ]

    # guard against no lid_selection
    if outname_lids != '' :
        outname_lids = os.path.join( config['summary_dir'], outname_lids )
        filenames.append(outname_lids)

    # file to append
    to_append = os.path.join( config['results_path'] )

    with open(to_append,'a') as outfile:
        for fname in filenames:
            if fname != to_append :
                with open(fname) as infile:
                    for line in infile:
                        outfile.write(line)

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
