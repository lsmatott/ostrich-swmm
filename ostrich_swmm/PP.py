"""Permeable Pavement Functions"""
import shapely.geometry
from collections import Counter

from math import floor, sqrt

from . import config as cfg
from . import units
import inject as inj
from .swmm import input as si
from . import LID

	
def add_pp(input_template, input_unit_system, lid, lid_id, count):
    """Inject parameters into a SWMM input template.
    Args:
        input_template (dict): The input to inject parameters into.
    Returns:
        pp_results, a list of lid(the pp properties) and excess_rb
    Note: Currently not impacted by the number of roofs
    """

    # Get the base subcatchment the barrel is located in.
    lid_base_sc_name = lid['location']['subcatchment']
    lid_base_sc = inj.get_subcatchment_definition(
         input_template,
         lid_base_sc_name,
    )
    if not lid_base_sc:
        raise cfg.ConfigException('Subcatchment "{0}" not found.'.format(lid_base_sc_name))
    # Generate a unique name for the LID's child subcatchment by checking against the names of existing subcatchments.
    lid_sc_name_index = 0
    lid_sc_name = '{0}##{1}'.format(lid_base_sc_name, lid_id)
    existing_lid_sc = inj.get_subcatchment_definition(
                input_template,
                lid_sc_name,
            )
    #naming subcatchments
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
    # Generate the child subcatchment for the LID and adjust the base subcatchment's properties to compensate.
    lid_sc = list(lid_base_sc)
    lid_sc[si.data_indices['SUBCATCHMENTS']['Name']] = lid_sc_name
    lid_sc[si.data_indices['SUBCATCHMENTS']['OutID']] = lid_base_sc_name
    #area units
    a_units=LID.area_units(input_unit_system)
    lid_area_unit = a_units[0]
    width_unit = a_units[1]
    sc_area_unit = a_units[2]
    lid_num_units = lid['number']
	
    sc_area_index = si.data_indices['SUBCATCHMENTS']['Area']
    sc_imperv_index = si.data_indices['SUBCATCHMENTS']['%Imperv']
    sc_width_index = si.data_indices['SUBCATCHMENTS']['Width']

    lid_base_sc_area = float(lid_base_sc[sc_area_index]) * sc_area_unit
    lid_base_sc_imperv = (float(lid_base_sc[sc_imperv_index])* units.registry.percent)
    lid_base_sc_imperv_area = lid_base_sc_imperv * lid_base_sc_area
    #figure out if there is too much permeable pavement being added - dependent on impervious area
    upper_bound = floor(float((lid_base_sc_imperv_area.to(lid_area_unit))/(lid['area']*lid_area_unit)))
    if upper_bound < 0:
	upper_bound = 0 

    excess = int(lid_num_units - upper_bound)
    if excess <= 0:
        excess = 0
    else: 
        lid_num_units = lid_num_units - excess
        print "OSTRICH input for subcat {0} had too many lid units, changing to max number {1}".format(lid_sc_name, lid_num_units)

    lid['number']= lid_num_units
	
    lid_total_area = lid_num_units * lid['area'] * lid_area_unit
    
    #adjust subcatchment areas after LIDs are added
    lid_sc_area = lid_total_area.to(sc_area_unit)
    new_lid_base_sc_area = lid_base_sc_area - lid_sc_area 
    lid_base_sc[sc_area_index] = new_lid_base_sc_area.magnitude
    lid_sc[sc_area_index] = lid_sc_area.magnitude

    new_lid_base_sc_imperv_area = lid_base_sc_imperv_area - lid_sc_area
    new_lid_base_sc_imperv = (new_lid_base_sc_imperv_area / new_lid_base_sc_area)

    lid_sc[sc_imperv_index] = 0
    lid_base_sc[sc_imperv_index] = (new_lid_base_sc_imperv.to('percent').magnitude)

    #adjust subcatchment widths
    lid_sc[sc_width_index]=(sqrt(lid_total_area/lid_area_unit))
    #New Subcatchment Width = Old Width * Non-LID Area / Original Area
    old_width = float(lid_base_sc[sc_width_index])
    new_width = old_width*(float(new_lid_base_sc_area/sc_area_unit)/float(lid_base_sc_area/sc_area_unit))
    lid_base_sc[sc_width_index]=new_width

    #adjust fromImp parameter
    #If the LID unit treats only direct rainfall, such as with a green roof, then this value should be 0.
    #This could be changed to reflect different situations
    lid['fromImp']=0
    
    # Set the LID subcatchment to the child subcatchment.
    lid['location']['subcatchment'] = lid_sc_name
    
    input_template['SUBCATCHMENTS']['lines'].append({
            'values': lid_sc,
            'comment': '{0} LID units. (Added by OSTRICH-SWMM.)'.format(
                    lid_num_units,
            ),
    })
    pp_results = [lid, excess, lid_base_sc]
    return pp_results
                    


           
     
       
