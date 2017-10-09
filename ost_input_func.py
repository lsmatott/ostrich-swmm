#Kristina Macro
#8/18/17
#Script Description:
#Functions for generating OSTRICH input files

#read in swmm inp file, returns list of subcat names
def get_subcats(swmm_inp_template, small_subcats):
    with open(swmm_inp_template) as swmm_input:
        block = []
        for line in swmm_input:
            if line.strip() == '[SUBCATCHMENTS]': 
                break
        for line in swmm_input: 
            if line.strip() == '[SUBAREAS]':
                break
            block.append(line)
    block = block[3:-1]
    subcat_list = []
    for i in range(0,len(block)):
        subcat_list.append(block[i].partition(' ')[0])
    for i in range(0,len(small_subcats)):
        subcat_list.remove(small_subcats[i])
    return subcat_list

#removes quotes from json dictionary value                    
def rm_quotes(line,position):
    jline = line.split(',')
    jline[position]=jline[position].split(': ')
    jline[position][1]=jline[position][1].replace('"','')
    jline[position] = jline[position][0]+": "+jline[position][1]
    newline = ", ".join(jline)
    return newline


    
