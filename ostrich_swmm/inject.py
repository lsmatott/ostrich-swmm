"""Functionality for injecting data into SWMM input files."""

from collections import Counter, defaultdict
import json
import logging
import csv
import platform
import shapely.geometry

from math import floor

# these imports don't work when debugging using VS Code
# from . import config as cfg
# from . import units
# from .swmm import input as si
# from .swmm import input_reader as sir
# from .swmm import input_writer as siw
# from . import LIDS

# use these imports when debugging using vs code
import config as cfg
import units
from swmm import input as si
from swmm import input_reader as sir
from swmm import input_writer as siw
import LIDS

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

    if sys.version_info[0] == 3:
        my_iter_items = subcatchment_polygon_coordinates.items()
    else:
        my_iter_items = subcatchment_polygon_coordinates.iteritems()

    return {
        subcatchment: shapely.geometry.Polygon(coordinates)
        for subcatchment, coordinates
        in my_iter_items
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

    if sys.version_info[0] == 3:
        my_iter_items = subcatchments.items()
    else:
        my_iter_items = subcatchments.iteritems()

    for subcatchment, polygon in my_iter_items:
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

    # lid_sc_info maps newly created subcatchments to corresponding LID info
    lid_sc_info = {}

    excess_lid =[]
    nlid = []
    sc_names_list = []
    all_lid_names = []

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

        # Get the name of the LID control
        lid_name = lid['name']
        if lid_name not in all_lid_names:
            all_lid_names.append(lid_name)
        if 'LID_CONTROLS' not in input_template:
            raise cfg.ConfigException(
                'There are no LID controls defined in the SWMM input file.',
            )
        lid_controls = input_template['LID_CONTROLS']
        lid_name_index = si.data_indices['LID_CONTROLS']['Common']['Name']
        lid_definition = [
            line
            for line
            in lid_controls['lines']
            if line['values']
            and line['values'][lid_name_index] == lid_name
        ]
        if not lid_definition:
            raise cfg.ConfigException(
                'No LID control named "{0}" was found in the SWMM input file.'.format(lid_name)
            )

        # Count the instance of this LID and give it an ID.
        lid_counter[lid_name] += 1
        lid_id = '{0}_{1}'.format(lid_name, lid_counter[lid_name])

        # Adjust the LID subcatchment as necessary.
        lid_type_index = si.data_indices['LID_CONTROLS']['Type']['Type']
        lid_type = lid_definition[0]['values'][lid_type_index]
        if lid['location']['subcatchment'] not in sc_names_list:
            sc_names_list.append(lid['location']['subcatchment'])

        # If the LID is a rain barrel...
        if lid_type == 'RB':
            rbcount = rbcount + 1
            if len( roofs ) == 0 :
                print("Warning - rain barrels are included in the configuration file")
                print("without a corresponding roof specification.")
                roof_sc = []
            else :
                roof_sc = LIDS.add_roofs(input_template, roofs, rbcount)
            rb_values = LIDS.add_rb(input_template, input_unit_system, lid, lid_id, roofs, roof_sc, rbcount)
            lid = rb_values[0]
            excess = rb_values[1]
            lid_base_sc = rb_values[2]
            excess_lid.append(excess)
            lid_num_units=lid['number']
        #permeable pavement
        elif lid_type == 'PP':
            pp_values = LIDS.add_pp(input_template, input_unit_system, lid, lid_id, count)
            lid = pp_values[0]
            excess = pp_values[1]
            lid_base_sc = pp_values[2]
            excess_lid.append(excess)
            lid_num_units=lid['number']
        #bio-retention cell
        elif lid_type == 'BC':
            bc_values = LIDS.add_bc(input_template, input_unit_system, lid, lid_id, count)
            lid = bc_values[0]
            excess = bc_values[1]
            lid_base_sc = bc_values[2]
            excess_lid.append(excess)
            lid_num_units=lid['number']
        #rain garden
        elif lid_type == 'RG':
             rg_values = LIDS.add_rg(input_template, input_unit_system, lid, lid_id, count)
             lid = rg_values[0]
             excess = rg_values[1]
             lid_base_sc = rg_values[2]
             excess_lid.append(excess)
             lid_num_units=lid['number']
        #vegetative swale
        elif lid_type == 'VS':
             vs_values = LIDS.add_vs(input_template, input_unit_system, lid, lid_id, count)
             lid = vs_values[0]
             excess = vs_values[1]
             lid_base_sc = vs_values[2]
             excess_lid.append(excess)
             lid_num_units=lid['number']
        #rooftop disconnection
        elif lid_type == 'RD':
             rd_values = LIDS.add_rd(input_template, input_unit_system, lid, lid_id, count)
             lid = rd_values[0]
             excess = rd_values[1]
             lid_base_sc = rd_values[2]
             excess_lid.append(excess)
             lid_num_units=lid['number']
        #green roof
        elif lid_type == 'GR':
             gr_values = LIDS.add_gr(input_template, input_unit_system, lid, lid_id, count)
             lid = gr_values[0]
             excess = gr_values[1]
             lid_base_sc = gr_values[2]
             excess_lid.append(excess)
             lid_num_units=lid['number']
        #infiltration trench
        elif lid_type == 'IT':
             it_values = LIDS.add_it(input_template, input_unit_system, lid, lid_id, count)
             lid = it_values[0]
             excess = it_values[1]
             lid_base_sc = it_values[2]
             excess_lid.append(excess)
             lid_num_units=lid['number']
##        #trees?
        else:
            logging.warning(
                (
                    'The LID control named {} is assigned a LID type of {} but that type '
                    'is not currently supported by ostrich-swmm.'
                    'Manual adjustments to other objects, such as '
                    'subcatchments, may be necessary.'
                ).format(lid_name, lid_type)
            )

        # Update the LID dictionary
        lid_info = {}
        lid_info['LidControlName'] = lid_name
        lid_info['NumInstances'] = 1
        lid_info['LidType'] = lid_type
        lid_info['NumUnits'] = lid_num_units
        lid_info['Excess'] = excess
        sc_name = lid['location']['subcatchment'] 
        if sc_name not in lid_sc_info :
            lid_sc_info[sc_name] = [ lid_info ]
        else :
            names = [ j[ 'LidControlName' ] for j in lid_sc_info[ sc_name ] ]
            if lid_name not in names :
                lid_sc_info[sc_name].append(lid_info)
            else :
                # This situation probably shoudn't occur because each LID is assigned
                # to it's own sub-catchment.
                lid_index = lid_sc_info[sc_name].index(lid_name)
                lid_sc_info[sc_name][lid_index]['NumInstances'] += 1
                lid_sc_info[sc_name][lid_index]['NumUnits'] += lid_info['NumUnits']
                lid_sc_info[sc_name][lid_index]['Excess'] += lid_info['Excess']

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
            lid['name'],
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

    # see https://stackoverflow.com/questions/30929363/csv-writerows-puts-newline-after-each-row    
    if platform.system == "Windows" :
        new_line = ''
    else :
        new_line = '\n'
    
    with open('num_lid.csv', 'w', newline=new_line) as outcsv:
        writer = csv.writer(outcsv)
        writer.writerow(["# Number of LID controls in each subcatchment"])
        header = ["Subcatchment_Name"]
        for i in all_lid_names:
            header.append(str(i))
        writer.writerow(header) 
        sum_line = ["Lid_Sum"]
        excess_line =["Excess_Lids"]
        for i in all_lid_names:
            sum_line.append(0)
            excess_line.append(0)
        for sc_name in lid_sc_info:
            line = []
            line.append(sc_name)   #need to figure out how to grab subcat coordinates
            sum_idx = 1
            for i in all_lid_names:
                num_units = 0
                num_excess = 0
                for j in lid_sc_info[sc_name] :
                    if j[ 'LidControlName' ] == i :
                        num_units = j[ 'NumUnits']
                        num_excess = j[ 'Excess']
                        break
                line.append(str(num_units))
                sum_line[sum_idx] += num_units
                excess_line[sum_idx] += num_excess
                sum_idx += 1
            writer.writerow(line)
        # convert sum and excess to string for writerow()
        sum_line = [ str(i) for i in sum_line ]
        excess_line = [ str(i) for i in excess_line ]
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
