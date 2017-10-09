#Kristina Macro
#8/17/17
#Script Description:
#Generates submodel_input_parameters.json.tpl file based submodel template swmm input file

import ost_input_func as f
small_subcats = ["SPP329#1", "SPP81#1", "SPP82#1"]
#remove_subcats = ["ECSD1#1", "ECSD4#1","WSSD13#1"]
subcat_list = f.get_subcats('submodel.template.inp', small_subcats)

types =["RB1","RB2"]
areas = [3.34,7.07]

NRB = []
param = []
for x in range(0, len(subcat_list)):
    for i in range(0, len(types)):
        NRB.append("_N{0}_{1}_".format(types[i],str(x)))
    param.append("_SUBCAT_{0}_".format(str(x)))

#generate json template file
import json
lids=[]
roofs = []
from collections import OrderedDict
n = -1
for x in range(0,len(subcat_list)):
    for i in range(0,len(types)):
        n = n+1
        lids.append(
            {"location": {"subcatchment": param[x]}, "type": types[i],"number": NRB[n], "area": areas[i],
                "width": 0, "initSat": 0, "fromImp": 1, "toPerv": 1})
        roofs.append(
            {"location": {"subcatchment": param[x]}, "type": "RF{0}".format(i+1), "number": NRB[n], "OutID": types[i],
             "area": 1655.23, "PctImperv": 100, "width": 43, "slope": 40,"NImp": 0.0115, "NPerv": 0.1,
             "PctZero": 100})
                     
with open("submodel_input_parameters.json.tpl", "w") as json_tpl:
    json_tpl.write("{\n")
    json_tpl.write('\t'+'"lids": ['+"\n")
    n=0
    for x in range(0,len(lids)):
        n= n+1
        if n < len(lids):
            newline = f.rm_quotes(json.dumps(lids[x]),6)
            json_tpl.write('\t'+'\t'+newline+","+'\n')
        else:
            newline = f.rm_quotes(json.dumps(lids[x]),6)
            json_tpl.write('\t'+'\t'+newline+'\n')
    json_tpl.write('\t'+"],"+ '\n')
    json_tpl.write('\t'+'"roofs": ['+"\n")
    n=0
    for x in range(0,len(roofs)):
        n= n+1
        if n < len(roofs):
            newrline = f.rm_quotes(json.dumps(roofs[x]),2)
            json_tpl.write('\t'+'\t'+newrline+","+'\n')
        else:
            newrline = f.rm_quotes(json.dumps(roofs[x]),2)
            json_tpl.write('\t'+'\t'+newrline+'\n')
    json_tpl.write('\t'+"]"+ '\n')
    json_tpl.write("}\n")

    
