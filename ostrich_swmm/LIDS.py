"""Functions for various LID types"""

# From SWMM5 User Manual:
#   BC for bio-retention cell --> add_bc() 
#   RG for rain garden --> add_rg()
#   GR for green roof --> add_gr()
#   IT for infiltration trench --> add_it()
#   PP for permeable pavement --> add_pp()
#   RB for rain barrel --> add_rb() and add_roofs()
#   RD for rooftop disconnection --> add_rd()
#   VS for vegetative swale --> add_vs()
#
import sys
import shapely.geometry
from collections import Counter

from math import floor, sqrt

# these imports don't work when debugging using vs code
# from . import config as cfg
# from . import units
# if sys.version_info[0] == 3 :
#     from . import inject as inj
# else :
#     import inject as inj
# from .swmm import input as si

# use these imports when debugging using vs code
import config as cfg
import units
if sys.version_info[0] == 3 :
    import inject as inj
else :
    import inject as inj
from swmm import input as si

# ------------------------------------------------------------------------------       
# General LID Functions
#   area_units() - determine units of measure (m^2, ft^2, acres, etc.)
#   add_roofs()  - for LIDs (e.g. rain barrels) that require roof insertion
#   add_lid_sc() - common actions for any LID addition ....
# ------------------------------------------------------------------------------

def area_units(input_unit_system):
    """Takes in input unit system and determines area units for
            lid and sc, returns A_units - a  
            list of lid area unit, width unit, and sc area unit"""
    if input_unit_system == 'US':
        lid_area_unit = 'square_feet'
        width_unit = 'feet'
        sc_area_unit = 'acres'
    elif input_unit_system == 'SI':
        lid_area_unit = 'square_meters'
        width_unit = 'meters'
        sc_area_unit = 'hectares'
    else:
        raise cfg.ConfigException(
            'Unknown unit system "{0}".'.format(input_unit_system),)
    A_units = [lid_area_unit,width_unit,sc_area_unit]
    return A_units

def add_roofs(input_template, roofs, count):
    """Makes rooftop connection for rainbarrels and other GI types, 
    returns roof_values"""
    if 'map' in roofs[count]['location']:
        if sc_polygons is None:
            sc_polygons = inj.extract_subcatchment_polygons(input_template)
        roofs[count]['location']['subcatchment'] = inj.get_subcatchment_from_map_coords(
            roofs[count]['location']['map'],
            sc_polygons,)
    roof_type = roofs[count]['type']
    # Count this instance of this roof type and give it an ID.
    n= count+1
    roof_id = '{0}_{1}'.format(roof_type, n)
    roof_base_sc_name = roofs[count]['location']['subcatchment']
    roof_base_sc = inj.get_subcatchment_definition(
        input_template,
        roof_base_sc_name,)
    if not roof_base_sc:
        raise cfg.ConfigException(
            'Subcatchment "{0}" not found.'.format(roof_base_sc_name))
    roof_sc_name_index = 0
    roof_sc_name = '{0}##{1}'.format(roof_base_sc_name, roof_id)
    existing_roof_sc = inj.get_subcatchment_definition(
        input_template,
        roof_sc_name,
    )
    while existing_roof_sc:
        existing_roof_sc = inj.get_subcatchment_definition(
                input_template,
                roof_sc_name,
        )
    roof_sc = list(roof_base_sc)
    roof_sc[si.data_indices['SUBCATCHMENTS']['Name']] = roof_sc_name

    return roof_sc

def add_lid_sc(input_template, input_unit_system, lid, lid_id, count, fromImp = 0, 
               roofs = None, roof_sc = None):
    """Inject parameters into a SWMM input template.
    Args:
        input_template (dict): The input to inject parameters into.
    Returns:
        lid_results, a list of lid properties and excess_lid information
    """

    # --------------------------------------------------------------------------
    # Get the base subcatchment the lid is located in.
    # --------------------------------------------------------------------------
    lid_base_sc_name = lid['location']['subcatchment']
    lid_base_sc = inj.get_subcatchment_definition(
         input_template,
         lid_base_sc_name,
    )
    if not lid_base_sc:
        raise cfg.ConfigException(
            'Subcatchment "{0}" not found.'.format(lid_base_sc_name))
    
    # --------------------------------------------------------------------------
    # Generate a unique name for the LID's child subcatchment by checking 
    # against the names of existing subcatchments.
    # --------------------------------------------------------------------------
    # initial try at obtaining a unique name
    lid_sc_name_index = 0
    lid_sc_name = '{0}##{1}'.format(lid_base_sc_name, lid_id)
    existing_lid_sc = inj.get_subcatchment_definition(
                input_template,
                lid_sc_name,
            )
    # naming loop: increase naming index until a unique name is created
    while existing_lid_sc:
        lid_sc_name_index += 1
        lid_sc_name = '{0}##{1}###{2}'.format(
            lid_base_sc_name,
            lid_id,
            lid_sc_name_index,)
        existing_lid_sc = inj.get_subcatchment_definition(
            input_template,
            lid_sc_name,
        )

    # --------------------------------------------------------------------------    
    # Generate the child subcatchment for the LIDs and adjust the base 
    # subcatchment properties to compensate. The procedure is as follows:
    #  1. Start with a copy of the base sub-catchment, coerced to a list
    #  2. Set the name of new sub-catchment (lid_sc_name)
    #  3. Route the outflow of the new LID sub-catchment (OutID) to the base sub-
    #     catchment
    #  4. Determine the units of measure for area and width
    #  5. Associate sub-catchment parameters with their units
    #  6. Determine excess and actual number of LIDs to be added
    #  7. Adjust area of parent sub-catchment to reflect LID addition - per SWMM
    #     best practices, the LIDs are added as a separate sub-catchment that
    #     drains into the base (parent) sub-catchment. Thus, the LID area must be
    #     subtracted from the impervious area of the parent sub-catchment. This 
    #     also results in a change in the %imperv value of the parent sub-
    #     catchment.
    # --------------------------------------------------------------------------
    lid_sc = list(lid_base_sc) 
    lid_sc[si.data_indices['SUBCATCHMENTS']['Name']] = lid_sc_name
    lid_sc[si.data_indices['SUBCATCHMENTS']['OutID']] = lid_base_sc_name
    #area units
    a_units=area_units(input_unit_system)
    lid_area_unit = a_units[0]
    width_unit = a_units[1]
    sc_area_unit = a_units[2]
    lid_num_units = lid['number']

    # --------------------------------------------------------------------------
    # optional roof information
    # --------------------------------------------------------------------------
    if (( roofs == None ) or ( len(roofs) == 0 )) :
        r_area = 0
        r_num_units = 0
        ind_roof = 0
    else:
        r_area = roofs[count]['area']
        r_num_units = roofs[count]['number']
        ind_roof = r_area
    
    # --------------------------------------------------------------------------
    # fetch list indices for the LID area, imperv, and width properties - this 
    # information is sotred in the si.data_indices dictionary.
    # --------------------------------------------------------------------------
    sc_area_index = si.data_indices['SUBCATCHMENTS']['Area']
    sc_imperv_index = si.data_indices['SUBCATCHMENTS']['%Imperv']
    sc_width_index = si.data_indices['SUBCATCHMENTS']['Width']

    # --------------------------------------------------------------------------
    # compute impervious area of the base subcatchment
    # --------------------------------------------------------------------------
    lid_base_sc_area = float(lid_base_sc[sc_area_index])
    lid_base_sc_imperv_pct = float(lid_base_sc[sc_imperv_index]) / 100.0
    lid_base_sc_imperv_area = lid_base_sc_imperv_pct * lid_base_sc_area
    
    # --------------------------------------------------------------------------
    # Figure out if there are too many LIDs being added - this is dependent on 
    # the impervious area under the assumption that each LID will be used to 
    # replace an impervious portion of the sub-catchment. Thus, the maximum 
    # number of LIDs that a sub-cathcment can support is equal to the amount of
    # impervious area in a sub-catchment divided by the area of a single LID plus
    # any area occupied by roofs that have also been extracted from the sub-
    # catchment.
    # --------------------------------------------------------------------------
    sc_lid_area = units.convert_from_sc_area_to_lid_area(lid_base_sc_imperv_area, sc_area_unit, lid_area_unit)
    upper_bound = floor(float(sc_lid_area/(ind_roof + lid['area'])))
    if upper_bound < 0 :
        upper_bound = 0 

    # compare max number of LIDs to the actual number and compute the excess
    excess = int(lid_num_units) - int(upper_bound)
    if excess <= 0:
        excess = 0
    else: 
        lid_num_units = int(upper_bound)
        print("OSTRICH input for subcat {0} had too many lid units, changing to max number {1}".format(lid_sc_name, lid_num_units))
        lid_area =  ind_roof + lid['area']
        print("OSTRICH input for subcat {0} - impervious area {1}".format(lid_sc_name, sc_lid_area))
        print("OSTRICH input for subcat {0} - lid area {1}".format(lid_sc_name, lid_area))
    
    # record the actual number of LIDs that will be added into the sub-catchment
    lid['number']= lid_num_units
    
    # compute the total area of all LID units that will be added
    lid_total_area = lid_num_units * lid['area']
    
    # --------------------------------------------------------------------------
    # handle optional inclusion of roofs in the LID sub-catchment 
    # --------------------------------------------------------------------------
    sc_out_index = si.data_indices['SUBCATCHMENTS']['OutID']
    if ( roofs == None ) or ( len( roofs ) == 0 ):
        r_num_units = 0
        roof_total_area = 0
        roof_sc_area = 0
        roof_values = [0,0,0,0,0,0,"",]
    else:
        r_num_units = lid_num_units
        roof_total_area = r_num_units * r_area
        roof_sc_area = units.convert_from_lid_area_to_sc_area(roof_total_area, lid_area_unit, sc_area_unit)
        roof_sc[sc_area_index]= roof_sc_area
        roof_sc[sc_imperv_index] = 100
        roof_sc[sc_out_index] = lid_sc_name
        roof_sc[sc_width_index] = sqrt(roof_total_area)
        ind_roof_sc_area = units.convert_from_lid_area_to_sc_area(ind_roof, lid_area_unit, sc_area_unit)
        fromImp = ( 100 * lid['number'] * ind_roof_sc_area ) / lid_base_sc_imperv_area
        #need to update roof values once excess has been taken out  
        roof_values = [roofs[count]['location']['subcatchment'],roofs[count]['NImp'],roofs[count]['NPerv'],0,0,roofs[count]['PctZero'],"OUTLET",]
        input_template['SUBAREAS']['lines'].append({
            'values': roof_values,
            'comment': None,
        })
        input_template['SUBCATCHMENTS']['lines'].append({
            'values': roof_sc,
            'comment': '{0} roof units. (Added by OSTRICH-SWMM.)'.format(r_num_units),
        })

    # --------------------------------------------------------------------------
    # adjust subcatchment area to compensate for LID additions
    # --------------------------------------------------------------------------
    lid_sc_area = units.convert_from_lid_area_to_sc_area(lid_total_area, lid_area_unit, sc_area_unit) 
    new_lid_base_sc_area = lid_base_sc_area - lid_sc_area - roof_sc_area
    lid_base_sc[sc_area_index] = new_lid_base_sc_area
    lid_sc[sc_area_index] = lid_sc_area

    # --------------------------------------------------------------------------
    # because LIDs are only installed on impervious areas it is necessary to 
    # adjust the %imperv value in the parent sub-catchment
    # --------------------------------------------------------------------------
    new_lid_base_sc_imperv_area = lid_base_sc_imperv_area - lid_sc_area - roof_sc_area
    
    # Guard against divide by zero, which can occur if entire subcatchment is allocated to the LID control
    if new_lid_base_sc_imperv_area > 0 :
        new_lid_base_sc_imperv = (new_lid_base_sc_imperv_area / new_lid_base_sc_area)
    else :
        new_lid_base_sc_imperv = 0.00

    lid_sc[sc_imperv_index] = 0
    lid_base_sc[sc_imperv_index] = 100 * new_lid_base_sc_imperv

    # --------------------------------------------------------------------------
    # Adjust LID and base subcatchment widths
    #    - The LID additions are assumed to be square (hence use of sqrt() in 
    #      the width calculation.
    #    - The width of the parent sub-catchment is multiplied by the  fraction 
    #      of area that remains after adding the LIDs. For example, suppose the 
    #      sub-catchment orginally has an area of 100 and a width of 10, and that
    #      30 units LID area are added, yielding a revised area of 100 - 30 = 70 
    #      in the parent sub-cathcment. Then the new width of the parent sub-
    #      catchment would be: 10 * (100 - 30) / 100 = 10 * 0.7 = 7
    # --------------------------------------------------------------------------
    lid_sc[sc_width_index]=sqrt(lid_total_area)
    #New Subcatchment Width = Old Width * Non-LID Area / Original Area
    old_width = float(lid_base_sc[sc_width_index])
    new_width = old_width * (new_lid_base_sc_area / lid_base_sc_area )
    lid_base_sc[sc_width_index] = new_width

    # --------------------------------------------------------------------------
    # adjust fromImp parameter
    #   Per the SWMM manual: fromImp is the percent of the impervious portion 
    #   of the subcatchment’s non-LID area whose runoff is treated by the LID 
    #   practice. (E.g., if rain barrels are used to capture roof runoff and 
    #   roofs represent 60% of the impervious area, then the impervious area 
    #   treated is 60%). If the LID unit treats only direct rainfall, such as 
    #   with a green roof, then this value should be 0. If the LID takes up the 
    #   entire subcatchment then this field is ignored.
    # --------------------------------------------------------------------------
    lid['fromImp'] = fromImp
    
    # Set the LID subcatchment to the child subcatchment.
    lid['location']['subcatchment'] = lid_sc_name
    
    input_template['SUBCATCHMENTS']['lines'].append({
            'values': lid_sc,
            'comment': '{0} LID units. (Added by OSTRICH-SWMM.)'.format(
                    lid_num_units,
            ),
    })
    lid_results = [lid, excess, lid_base_sc]
    return lid_results
                      
# --------------------------------------------------------------------------------
# Rain Barrel Functions
#    add_rb()
# ---------------------------------------------------------------------------------
def add_rb(input_template, input_unit_system, lid, lid_id, roofs, roof_sc, count):
    """Inject parameters into a SWMM input template.
    Args:
        input_template (dict): The input to inject parameters into.
    Returns:
        rb_results, a list of lid(the rb properties), excess_rb, and
        lid_base_sc, the updated version of the base subcatchment after rb are added
    """

    # invoke helper function to add rain barrels
    rb_results = add_lid_sc(input_template, input_unit_system, lid, lid_id, count, 1, roofs, roof_sc)

    return rb_results
                    
# -----------------------------------------------------------------------
# Permeable Pavement Functions
#   add_pp()
# -----------------------------------------------------------------------
def add_pp(input_template, input_unit_system, lid, lid_id, count):
    """Inject parameters into a SWMM input template.
    Args:
        input_template (dict): The input to inject parameters into.
    Returns:
        pp_results, a list of lid (the pp properties) and excess_pp
    Note: Currently not impacted by the number of roofs
    """

    # invoke helper function to add porous pavement
    pp_results = add_lid_sc(input_template, input_unit_system, lid, lid_id, count)

    return pp_results

# -----------------------------------------------------------------------
# Bio Retencion Cell Functions
#   add_bc()
# -----------------------------------------------------------------------
def add_bc(input_template, input_unit_system, lid, lid_id, count):
    """Inject parameters into a SWMM input template.
    Args:
        input_template (dict): The input to inject parameters into.
    Returns:
        bc_results, a list of lid (the bc properties) and excess_bc
    Note: Currently not impacted by the number of roofs
    """
    
    # invoke helper function to add bio retention cells
    bc_results = add_lid_sc(input_template, input_unit_system, lid, lid_id, count)

    return bc_results

# -----------------------------------------------------------------------
# Green Roof Functions
#   add_gr()
# -----------------------------------------------------------------------
def add_gr(input_template, input_unit_system, lid, lid_id, count):
    """Inject parameters into a SWMM input template.
    Args:
        input_template (dict): The input to inject parameters into.
    Returns:
        gr_results, a list of lid (the gr properties) and excess_gr
    Note: Currently not impacted by the number of roofs
    """
    
    # invoke helper function to add green roofs
    gr_results = add_lid_sc(input_template, input_unit_system, lid, lid_id, count)

    return gr_results

# -----------------------------------------------------------------------
# Infiltration Trench Functions
#   add_it()
# -----------------------------------------------------------------------
def add_it(input_template, input_unit_system, lid, lid_id, count):
    """Inject parameters into a SWMM input template.
    Args:
        input_template (dict): The input to inject parameters into.
    Returns:
        it_results, a list of lid (the it properties) and excess_it
    Note: Currently not impacted by the number of roofs
    """
    
    # invoke helper function to add infiltration trenches
    it_results = add_lid_sc(input_template, input_unit_system, lid, lid_id, count)

    return it_results

# -----------------------------------------------------------------------
# Rooftop Disconnect Functions
#   add_rd()
# -----------------------------------------------------------------------
def add_it(input_template, input_unit_system, lid, lid_id, count):
    """Inject parameters into a SWMM input template.
    Args:
        input_template (dict): The input to inject parameters into.
    Returns:
        rd_results, a list of lid (the rd properties) and excess_rd
    Note: Currently not impacted by the number of roofs
    """
    
    # invoke helper function to add rooftop disconnects
    rd_results = add_lid_sc(input_template, input_unit_system, lid, lid_id, count)

    return rd_results

# -----------------------------------------------------------------------
# Vegetative Swale Functions
#   add_vs()
# -----------------------------------------------------------------------
def add_vs(input_template, input_unit_system, lid, lid_id, count):
    """Inject parameters into a SWMM input template.
    Args:
        input_template (dict): The input to inject parameters into.
    Returns:
        it_results, a list of lid (the it properties) and excess_it
    Note: Currently not impacted by the number of roofs
    """
    
    # invoke helper function to add vegetative swales
    vs_results = add_lid_sc(input_template, input_unit_system, lid, lid_id, count)

    return vs_results
