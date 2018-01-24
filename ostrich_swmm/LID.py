"""General LID Functions"""
import shapely.geometry
from collections import Counter

from math import floor, sqrt

from . import config as cfg
from . import units
import inject as inj
from .swmm import input as si

def area_units(input_unit_system):
    """Takes in input unit system and determines area units for
            lid and sc, returns A_units, 
            list of lid area unit and sc area unit"""
    if input_unit_system == 'US':
        lid_area_unit = units.registry.ft ** 2
        width_unit = units.registry.ft
        sc_area_unit = units.registry.acre
    elif input_unit_system == 'SI':
        lid_area_unit = units.registry.m ** 2
        width_unit = units.registry.m
        sc_area_unit = units.registry.hectare
    else:
        raise cfg.ConfigException(
            'Unknown unit system "{0}".'.format(input_unit_system),)
    A_units = [lid_area_unit,width_unit,sc_area_unit]
    return A_units

                    
def add_roofs(input_template, roofs, count):
    """Makes rooftop connection for rainbarrels, 
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

           
     
       
