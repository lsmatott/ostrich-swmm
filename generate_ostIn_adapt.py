#Kristina Macro
#10/04/17
#Script Description:
#Generates parameters for OSTRICH input file and submodel_input_parameters.json.tpl file
#based submodel template swmm input file

import ost_input_func as f
#small_subcats = ["SPP329#1", "SPP81#1", "SPP82#1"]
remove_subcats = ["ECSD1#1", "ECSD4#1","WSSD13#1"]
subcat_list = f.get_subcats('submodel.template.inp', remove_subcats)


initial_rb = 1
lower_rb = 0
upper_rb = 2000
upper_list = [254, 2000, 153, 2000, 352, 2000, 430, 2000, 68, 2000, 2000, 2000, 2000, 85, 102, 2000, 438, 2000, 153, 2000, 147, 2000, 172, 2000,
 328, 2000, 2000, 2000, 102, 2000, 462, 2000, 352, 2000, 47, 2000, 52, 2000, 219, 2000, 597, 2000, 372, 2000, 283, 2000, 172, 2000,
 178, 2000, 324, 2000, 365, 2000, 107, 2000, 304, 2000, 386, 2000, 319, 2000, 281, 2000, 51, 2000, 219, 2000, 80, 2000, 276, 2000,
 156, 2000, 372, 2000, 367, 2000, 279, 2000, 2000, 42, 644, 2000, 358, 2000, 525, 2000, 68, 2000, 99, 2000, 209, 2000, 424, 2000, 43,
 2000, 180, 2000, 322, 2000, 241, 2000, 245, 2000, 226, 2000, 315, 2000, 160, 2000, 302, 2000, 2000, 165, 42, 2000, 198, 2000, 72,
 2000, 179, 2000, 135, 2000, 313, 2000, 243, 2000, 333, 2000, 52, 2000, 646, 2000, 287, 2000, 102, 2000, 166, 2000, 118, 2000, 18,
 2000, 19, 2000, 2000, 45, 165, 2000, 96, 2000, 159, 2000, 110, 2000, 44, 2000, 2000, 119, 178, 2000, 169, 2000, 2000, 27, 28, 2000,
 182, 2000, 33, 2000, 307, 2000, 232, 2000, 218, 2000, 467, 2000, 126, 2000, 13, 2000, 68, 2000, 33, 2000, 388, 2000, 235, 2000, 438,
 2000, 451, 2000, 173, 2000, 128, 2000, 101, 2000, 519, 2000, 389, 2000, 315, 2000, 103, 2000, 395, 2000, 2000, 90, 162, 2000, 49,
 2000, 461, 2000, 1159, 2000, 72, 2000, 358, 2000, 576, 2000, 449, 2000, 199, 2000, 161, 2000, 382, 2000, 390, 2000, 275, 2000, 2000,
 18, 192, 2000, 236, 2000, 377, 2000, 2000, 178, 500, 2000, 188, 2000, 229, 2000, 360, 2000, 327, 2000, 149, 2000, 2000, 252, 2000,
 383, 2000, 12, 137, 2000, 180, 2000, 2000, 2000, 2000, 2000, 563, 2000, 170, 2000, 273, 2000, 160, 2000, 64, 2000, 30, 2000, 41,
 2000, 55, 2000, 33, 2000, 37, 2000, 9, 2000, 46, 2000, 78, 2000, 2000, 17, 4, 2000, 3,2000, 41, 2000, 14, 2000, 67, 2000, 124, 2000,
 37, 2000, 52, 2000, 27, 2000, 11, 2000, 28, 2000, 71, 2000, 2000, 2000]
types =["RB1","RB2"]
init =[[0,0]]
rbcosts = [150,400]

#generate OSTRICH input
with open("ostIn.txt", "w") as ostIn:
    programtype= "ModelEvaluation"
    ostIn.write("ProgramType " + programtype.strip('"')+'\n')
    ostIn.write("ModelExecutable ./ostrich-swmm.sh\n")
    ostIn.write("ModelSubdir mod\n")
    ostIn.write("ObjectiveFunction GCOP\n")
    ostIn.write("PreserveModelOutput no\n")
    ostIn.write(" \n")
    ostIn.write("BeginFilePairs\n")
    ostIn.write("submodel_input_parameters.json.tpl; submodel_input_parameters.json\n")
    ostIn.write("EndFilePairs\n")
    ostIn.write(" \n")
    ostIn.write("BeginExtraFiles\nsubmodel-ostrich-swmm-config.json\nsubmodel.template.inp\nTY_1993_Modified.dat\nTY_1993_Unmodified.dat\nEndExtraFiles\n")
    ostIn.write(" \n")
    ostIn.write("BeginIntegerParams\n")
    NRB = []
    n = -1
    for x in range(0, len(subcat_list)):
        for i in range(0, len(types)):
            n= n+1
            NRB.append("_N{0}_{1}_".format(types[i],str(x)))
            ostIn.write("_N{0}_{1}_".format(types[i],str(x))+ '\t'+ str(initial_rb)+'\t'+ str(lower_rb)+ '\t'+ str(upper_rb) +'\n')
            #ostIn.write("_N{0}_{1}_".format(types[i],str(x))+ '\t'+ str(initial_rb)+'\t'+ str(lower_rb)+ '\t'+ str(upper_list[n]) +'\n')
    ostIn.write("EndIntegerParams\n")
    ostIn.write(" \n")
    ostIn.write("BeginCombinatorialParams\n")
    param = []
    for x in range(0,len(subcat_list)):
        param.append("_SUBCAT_{0}_".format(str(x)))
        ostIn.write("_SUBCAT_{0}_".format(str(x))+ '\t'+"string"+ '\t'+(subcat_list[x].strip('"'))+ '\t'+"1"+ '\t'
                                +(subcat_list[x].strip('"'))+'\n')
    ostIn.write("EndCombinatorialParams\n")
    ostIn.write(" \n")
    ostIn.write("BeginResponseVars\n")
    ostIn.write("#name   filename             keyword         line    col     token  aug?\n")
    ostIn.write("NCSO    submodel_nodes.csv ; node_name       1       2       ','    no\n")
    ostIn.write("FVOL    submodel_nodes.csv ; node_name       1       3       ','    yes\n")
    ostIn.write("FDUR    submodel_nodes.csv ; node_name       1       4       ','    yes\n")
    n= -1
    for x in range(0,len(subcat_list)):
        for i in range(0, len(types)):
            n= n+1
            ostIn.write(str(NRB[n])+"n" + '\t' + "num_lid.csv ;"+ '\t'+ "Subcat_Name" + '\t'+ str(x+1) + '\t'+ str(i+1)+ '\t' + "','    no\n")
    ostIn.write("EndResponseVars\n")
    ostIn.write(" \n")
    ostIn.write("BeginGCOP\nCostFunction NCSO\nPenaltyFunction APM\nEndGCOP\n")
    ostIn.write(" \n")
    ostIn.write("BeginConstraints\n")
    n =-1
    for x in range(0, len(subcat_list)):
        for i in range(0, len(types)):
            n= n+1
            ostIn.write("Con{0}".format(n)+ '\t' + "general"+ '\t'+ str(rbcosts[i])+ '\t'+"0.00" + '\t'+ "0.00"+ '\t'+ str(NRB[n])+"n"+'\n')
##        ostIn.write("Con{0}".format(x)+ '\t' + "general"+ '\t'+ "1E6"+ '\t'+"0.00" + '\t'+ "0.00"+ '\t'+ excess_var_list[x]+'\n')
    ostIn.write("EndConstraints\n")
    ostIn.write(" \n")
    ostIn.write("BeginInitParams\n")
    for row in range(0, len(init)):
        numrb = [init[row][0],init[row][1]]*len(subcat_list)
        numsubcat = [0]*len(subcat_list)
        ostIn.write(('{} '*len(numrb)).format(*numrb))
        ostIn.write((('{} '*len(numsubcat)).format(*numsubcat))+'\n')
    ostIn.write("EndInitParams\n")
    

