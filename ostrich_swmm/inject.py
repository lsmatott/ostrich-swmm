"""Functionality for injecting data into SWMM input files."""

from collections import Counter, defaultdict
import json
import logging
import csv

import shapely.geometry

from math import floor

from . import config as cfg
from . import units

from .swmm import input as si
from .swmm import input_reader as sir
from .swmm import input_writer as siw

# import LID addition codes
from . import LIDS

input_parameters_schema_path = None
"""The path to the JSON Schema used to validate input parameters."""


def extract_subcatchment_polygons(swmm_input):
    """Extract subcatchment polygons from SWMM input.

    Args:
        swmm_input (dict): The input to extract subcatchment polygons from.

    Returns:
        dict: A mapping of subcatchment names to Shapely polygons.
    """
    subcatchment_polygon_coordinates = defaultdict(list)

    polygon_sc_index = si.data_indices['POLYGONS']['Subcat']
    polygon_x_index = si.data_indices['POLYGONS']['Xcoord']
    polygon_y_index = si.data_indices['POLYGONS']['Ycoord']

    swmm_input_polygon_lines = swmm_input.get('POLYGONS', {
        'lines': [],
    })['lines']
    for line in swmm_input_polygon_lines:
        values = line['values']
        if not values:
            continue
        subcatchment_polygon_coordinates[values[polygon_sc_index]].append(
            (
                float(values[polygon_x_index]),
                float(values[polygon_y_index]),
            ),
        )

    return {
        subcatchment: shapely.geometry.Polygon(coordinates)
        for subcatchment, coordinates
        in subcatchment_polygon_coordinates.iteritems()
    }


def get_subcatchment_definition(swmm_input, sc_name):
    """Get a subcatchment definition from SWMM input.

    Args:
        swmm_input (dict): The input to extract a subcatchment definition from.
        sc_name (string): The name of the subcatchment to extract.

    Returns:
        list|None: The input file definition for the subcatchment or None if
            not found.
    """
    if 'SUBCATCHMENTS' not in swmm_input:
        return None

    sc_name_index = si.data_indices['SUBCATCHMENTS']['Name']
    return next((
        line['values']
        for line
        in swmm_input['SUBCATCHMENTS']['lines']
        if line['values'] and line['values'][sc_name_index] == sc_name
    ), None)


def get_subcatchment_from_map_coords(coordinates, subcatchments):
    """Get the subcatchment a set of map coordinates falls within.

    Args:
        coordinates (dict): A set of map coordinates. (Keys are x, y.)
        subcatchments (dict): A mapping of subcatchments to Shapely Polygons.

    Returns:
        string: The subcatchment the point falls within.

    Raises:
        ValueError: The point did not fall within any given subcatchments.
    """
    point = shapely.geometry.Point(coordinates['x'], coordinates['y'])
    for subcatchment, polygon in subcatchments.iteritems():
        if polygon.contains(point):
            return subcatchment

    raise ValueError(
        "Coordinates ({0}, {1}) not found in subcatchments.".format(
            point.x,
            point.y,
        )
    )


def inject_parameters_into_input(input_parameters, input_template):
    """Inject parameters into a SWMM input template.

    Args:
        input_parameters (dict): The parameters to inject.
        input_template (dict): The input to inject parameters into.

    Raises:
        ConfigException: The configuration is invalid.
    Returns:
        excess_rb for input into extract csv
    """
    global input_parameters_schema_path
    if input_parameters_schema_path is None:
        input_parameters_schema_path = cfg.get_package_json_schema_path(
            'parameters.schema.json',
        )

    # Validate the input parameters against the JSON Schema.
    cfg.validate_against_json_schema(
        input_parameters,
        input_parameters_schema_path,
    )

    # Get useful input options.
    input_unit_system = si.get_unit_system(input_template)

    # Create a variable to hold the subcatchment polygons, but wait to populate
    # it until needed.
    sc_polygons = None

    # For each LID in the input parameters...
    lids = input_parameters.get("lids", [])
    lid_counter = Counter()
    #add in rooftop connections
    roofs = input_parameters.get("roofs", [])
    count = -1
    rbcount = -1

    excess_lid =[]
    nlid = []
    sc_names_list = []
    all_lid_types = []

    for lid in lids:
        count = count + 1
        # If the location is given in map coordinates, convert to subcatchment.
        if 'map' in lid['location']:
            if sc_polygons is None:
                sc_polygons = extract_subcatchment_polygons(input_template)
            lid['location']['subcatchment'] = get_subcatchment_from_map_coords(
                lid['location']['map'],
                sc_polygons,
            )

        # If the drain point is given in map coordinates, convert to subcatch.
        if 'drainTo' in lid and 'map' in lid['drainTo']:
            if sc_polygons is None:
                sc_polygons = extract_subcatchment_polygons(input_template)
            lid['drainTo']['subcatchment'] = get_subcatchment_from_map_coords(
                lid['drainTo']['map'],
                sc_polygons,
            )

        # Get the LID's type.
        lid_type = lid['type']
        if lid_type not in all_lid_types:
            all_lid_types.append(lid_type)
        if 'LID_CONTROLS' not in input_template:
            raise cfg.ConfigException(
                'There are no LID controls defined in the SWMM input file.',
            )
        lid_controls = input_template['LID_CONTROLS']
        lid_type_name_index = si.data_indices['LID_CONTROLS']['Common']['Name']
        lid_type_definition = [
            line
            for line
            in lid_controls['lines']
            if line['values']
            and line['values'][lid_type_name_index] == lid_type
        ]
        if not lid_type_definition:
            raise cfg.ConfigException(
                'LID type "{0}" not found in SWMM input file.'.format(lid_type)
            )

        # Count this instance of this LID type and give it an ID.
        lid_counter[lid_type] += 1
        lid_id = '{0}_{1}'.format(lid_type, lid_counter[lid_type])

        # Adjust the LID's subcatchment as necessary.
        lid_type_type_index = si.data_indices['LID_CONTROLS']['Type']['Type']
        lid_type_type = lid_type_definition[0]['values'][lid_type_type_index]
        if lid['location']['subcatchment'] not in sc_names_list:
            sc_names_list.append(lid['location']['subcatchment'])
        
        # If the LID is a rain barrel...
        if lid_type_type == 'RB':
            rbcount = rbcount + 1
            roof_sc = LIDS.add_roofs(input_template,roofs, rbcount)
            rb_values = LIDS.add_rb(input_template, input_unit_system, lid, lid_id, roofs, roof_sc, rbcount)
            lid = rb_values[0]
            excess = rb_values[1]
            lid_base_sc = rb_values[2]
            excess_lid.append(excess)
            lid_num_units=lid['number']
        #permeable pavement
        elif lid_type_type == 'PP':
            pp_values = LIDS.add_pp(input_template, input_unit_system, lid, lid_id, count)
            lid = pp_values[0]
            excess = pp_values[1]
            lid_base_sc = pp_values[2]
            excess_lid.append(excess)
            lid_num_units=lid['number']
##        #rain garden
##        elif lid_type_type == 'RG':
##        #vegetative swale
##        elif lid_type_type == 'VS':
##        #rooftop disconnection
##        elif lid_type_type == 'RD':
##        #green roof
##        elif lid_type_type == 'GR':
##        #infiltration trench
##        elif lid_type_type == 'IT':
##        #trees?

        else:
            logging.warning(
                (
                    'LID type "{0}" is not directly supported by this module. '
                    'Manual adjustments to other objects, such as '
                    'subcatchments, may be necessary.'
                ).format(lid_type_type)
            )

        # Add the LID to the input.
        lid_drain_to = ''
        if 'drainTo' in lid:
            lid_drain_to_obj = lid['drainTo']
            if 'subcatchment' in lid_drain_to_obj:
                lid_drain_to = lid_drain_to_obj['subcatchment']
            elif 'node' in lid_drain_to_obj:
                lid_drain_to = lid_drain_to_obj['node']
        
        nlid.append(lid_num_units)
        
        lid_values = [
            lid['location']['subcatchment'],
            lid['type'],
            lid['number'],
            lid['area'],
            lid['width'],
            lid['initSat'],
            lid['fromImp'],
            lid['toPerv'],
            lid.get('rptFile', ''),
            lid_drain_to,
        ]
        if 'LID_USAGE' not in input_template:
            input_template['LID_USAGE'] = {
                'lines': [],
                'comment': None,
            }

        input_template['LID_USAGE']['lines'].append({
            'values': lid_values,
            'comment': None,
        })
        
    with open('num_lid.csv', 'wb') as outcsv:
        writer = csv.writer(outcsv)
        header = ["Subcat_Name"]
        nlid_col = []
        nexcess =[]
        for i in range(0, len(all_lid_types)):
            header.append(str(all_lid_types[i]))
            nlid_col.append(nlid[i:len(nlid):len(all_lid_types)])
            nexcess.append(excess_lid[i:len(excess_lid):len(all_lid_types)])
        writer.writerow(header) 
        line = []
        for i in range(0, len(sc_names_list)):
            line.append(sc_names_list[i])   #need to figure out how to grab subcat coordinates
            for j in range(0, len(nlid_col)):
                line.append(str(nlid_col[j][i]))
            writer.writerow(line)
            line =[]
        sum_line = ["Lid Sum"]
        excess_line =["Excess Lids"]
        for i in range(0, len(nlid_col)):
            sum_line.append(str(sum(nlid_col[i])))
            excess_line.append(str(sum(nexcess[i])))
        writer.writerow(sum_line) 
        writer.writerow(excess_line)
        


def perform_injection(config, validate=True):
    """Perform the injection as specified in a configuration.

    Args:
        config: The config to get injection configuration from.
        validate (boolean): Validate the configuration before attempting
            to use it. Defaults to True.

    Raises:
        ConfigException: The configuration is invalid.
        IOError: An error occurred during reading or writing.
    """
    if validate:
        validate_config(config)

    with open(config['input_template_path']) as input_template_file:
        input_template = sir.read(input_template_file)

    with open(config['input_parameters_path']) as input_parameters_file:
        input_parameters = json.load(input_parameters_file)

    inject_parameters_into_input(input_parameters, input_template)

    with open(config['input_path'], 'w') as input_file:
        siw.write(input_template, input_file)


def validate_config(config):
    """Validate a configuration for use with this functionality.

    Args:
        config (dict): The configuration to validate.

    Raises:
        ConfigException: The configuration is invalid.
    """
    cfg.validate_required_sections(config, [
        'input_path',
        'input_template_path',
        'input_parameters_path',
    ], 'inject')
    cfg.validate_file_exists(config, 'input_template_path')
    cfg.validate_file_exists(config, 'input_parameters_path')
    cfg.validate_dir_exists(config, 'input_path', path_is_file=True)
