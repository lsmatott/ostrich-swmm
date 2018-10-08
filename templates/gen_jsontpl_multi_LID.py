#Script Description:
#Generates submodel_input_parameters.json.tpl file based on template swmm input file

import ost_input_func as f

#take out subcats that shouldn't be included in optimization
remove_subcats = []
subcat_list = f.get_subcats('ModelTemplate.inp', remove_subcats)

types = f.get_LIDs('ModelTemplate.inp')

#define LID areas
areas = [3.34,100]

NLID = []
param = []
for x in range(0, len(subcat_list)):
    for i in range(0, len(types)):
        NLID.append("_N{0}_{1}_".format(types[i],str(x)))
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
            {"location": {"subcatchment": param[x]}, "type": types[i],"number": NLID[n], "area": areas[i],
                "width": 0, "initSat": 0, "fromImp": 1, "toPerv": 1})
        if types[i][0:2]=='RB':
            roofs.append(
                {"location": {"subcatchment": param[x]}, "type": "RF{0}".format(i+1), "number": NLID[n], "OutID": types[i],
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

    
