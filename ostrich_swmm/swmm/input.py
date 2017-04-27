"""Common functionality for handling SWMM input."""

section_formats = {
    '': 'txt',
    'TITLE': 'txt',
    'CONTROLS': 'txt',
}
"""The formats for each section. If not specified, assume space-separated."""

data_indices = {
    'OPTIONS': {
        'Name': 0,
        'Value': 1,
    },
    'SUBCATCHMENTS': {
        'Name': 0,
        'Rgage': 1,
        'OutID': 2,
        'Area': 3,
        '%Imperv': 4,
        'Width': 5,
        'Slope': 6,
        'Clength': 7,
        'Spack': 8,
    },
    'LID_CONTROLS': {
        'Common': {
            'Name': 0,
        },
        'Type': {
            'Type': 1,
        },
    },
    'POLYGONS': {
        'Subcat': 0,
        'Xcoord': 1,
        'Ycoord': 2,
    },
}
"""The indices of values for input lines."""


def get_section_format(section):
    """Get the format for a section.

    Args:
        section (string): The section to get the format for.

    Returns:
        string: The format of the given section.
    """
    return section_formats.get(section, 'ssv')


def get_flow_units(swmm_input):
    """Get the flow units used by the given input.

    Args:
        swmm_input (dict): The input to extract the flow units from.

    Returns:
        string: The flow units being used by the input.
    """
    flow_units = 'CFS'
    if 'OPTIONS' in swmm_input:
        options_name_index = data_indices['OPTIONS']['Name']
        flow_units_line = next((
            line
            for line
            in swmm_input['OPTIONS']['lines']
            if line['values']
            and line['values'][options_name_index] == 'FLOW_UNITS'
        ), None)

        if flow_units_line:
            options_value_index = data_indices['OPTIONS']['Value']
            flow_units = flow_units_line['values'][options_value_index]

    return flow_units


def get_unit_system(swmm_input):
    """Get the unit system used by the given input.

    Args:
        swmm_input (dict): The input to extract the unit system from.

    Returns:
        string: The unit system being used by the input.

    Raises:
        ValueError: The flow units used by the input are not recognized.
    """
    flow_units = get_flow_units(swmm_input)

    if flow_units in {'CFS', 'GPM', 'MGD'}:
        return 'US'
    elif flow_units in {'CMS', 'LPS', 'MLD'}:
        return 'SI'

    raise ValueError('Unrecognized flow units "{0}".'.format(flow_units))
