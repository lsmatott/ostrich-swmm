"""Common functionality for handling units."""

def convert_from_sc_area_to_lid_area(sc_area, sc_area_unit, lid_area_unit):
    # same units, no conversion needed
    if sc_area_unit == lid_area_unit :
        return sc_area

    if sc_area_unit == "acres" :
        if lid_area_unit == "square_feet" :
            return sc_area * 43560
    elif sc_area_unit == "hectares" :
        if lid_area_unit == "square_meters" :
            return sc_area * 10000

    print("error in convert_from_sc_area_to_lid_area()")
    print("   Don't know how to convert from {} to {}".format(sc_area_unit, lid_area_unit))
    return 0

def convert_from_lid_area_to_sc_area(lid_area, lid_area_unit, sc_area_unit):
    # same units, no conversion needed
    if sc_area_unit == lid_area_unit :
        return lid_area

    if sc_area_unit == "acres" :
        if lid_area_unit == "square_feet" :
            return lid_area / 43560
    elif sc_area_unit == "hectares" :
        if lid_area_unit == "square_meters" :
            return lid_area / 10000

    print("error in convert_from_lid_area_to_sc_area()")
    print("   Don't know how to convert from {} to {}".format(lid_area_unit, sc_area_unit))
    return 0
