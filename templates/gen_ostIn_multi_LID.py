#Script Description:
#Generates parameters for OSTRICH input file and submodel_input_parameters.json.tpl file
#based on template swmm input file

import ost_input_func as f
import csv

remove_subcats = []
subcat_list = f.get_subcats('ModelTemplate.inp', remove_subcats)

initial = 1
lower_bound = 0
upper_bound = 500
types =f.get_LIDs('ModelTemplate.inp')

costs = [150,400]

#generate OSTRICH input
with open("ostIn.txt", "w") as ostIn:
    programtype= "ParaPADDS"
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
    ostIn.write("BeginExtraFiles\nsubmodel-ostrich-swmm-config.json\nModelTemplate.inp\nEndExtraFiles\n")
    ostIn.write(" \n")
    #integer parameters
    ostIn.write("BeginIntegerParams\n")
    NLID = []
    n = -1
    for x in range(0, len(subcat_list)):
        for i in range(0, len(types)):
            n= n+1
            NLID.append("_N{0}_{1}_".format(types[i],str(x)))
            ostIn.write("_N{0}_{1}_".format(types[i],str(x))+ '\t'+ str(initial)+'\t'+ str(lower_bound)+ '\t'+ str(upper_bound) +'\n')
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
    sum_n = []
    for i in range(0, len(types)):
        ostIn.write("SUM_N{0}".format(types[i])+'\tnum_lid.csv ;	Subcat_Name'+'\t'+str(len(subcat_list)+1)+'\t'+str(i+2)+ "\t','    no\n")
        ostIn.write("Excess{0}".format(types[i])+"\tnum_lid.csv ;	Subcat_Name"+'\t'+str(len(subcat_list)+2)+'\t'+str(i+2)+"\t','    no\n")
        sum_n.append("SUM_"+"N{0}".format(types[i]))
    ostIn.write("EndResponseVars\n")
    ostIn.write(" \n")
    #add tied response for real cost
    ostIn.write("BeginTiedResponseVars\n")
    #<name1> <np1> <pname1,1> <pname1,2> ... <pname1,np1> <type1> <type_data1>
    ostIn.write("Real_Cost" + '\t'+str(len(types))+ '\t'+"\t".join(map(str,sum_n))+ '\t'+"wsum\t"+"\t".join(map(str,costs))+"\n")
    ostIn.write("EndTiedResponseVars\n")
    ostIn.write(" \n")
    ostIn.write("BeginGCOP\nCostFunction NCSO\nPenaltyFunction APM\nEndGCOP\n")
    ostIn.write(" \n")
    ostIn.write("BeginConstraints\n")
    #cost constraint
    ostIn.write("Cost_Constraint" + '\t' + "general 1E6"+ '\t'+"0.00" + '\t'+ "30000"+ '\t'+ "Real_Cost\n")
    n=0
    for i in range(0, len(types)):
        n=n+1
        ostIn.write("Excess_Con{0}".format(n)+"\tgeneral 1E6	0.00	0.00"+'\t'+ "Excess{0}".format(types[i])+"\n")
    ostIn.write("EndConstraints\n")
    ostIn.write(" \n")
    ostIn.write("BeginParallelDDSAlg\nPerturbationValue 0.2\nMaxIterations 75\nSelectionMetric Random\nEndParallelDDSAlg")
  

