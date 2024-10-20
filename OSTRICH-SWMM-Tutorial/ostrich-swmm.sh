#!/bin/bash

#
# Optional: load necessary modules
#
noModules=`type module 2>&1 | grep "not found" | wc -l`
if [ "$noModules" == "0" ]; then
  echo "Loading modules ..."
  module load intel
  module load anaconda/python
  module load swmm5
fi

#
# Optional: setup PATH variable
#
# Hint: adjust the paths below to match where
# swmm5 and ostrich-swmm are installed.
#
if [ "$noModules" == "1" ]; then
  echo "Setting paths ..."
  export PATH=$HOME/mygit/ostswmm/bin:$PATH
  export PATH=$HOME/swmm5/bin:$PATH
fi

#
# Activate the ostswmm python environment
#
# Hint: use "conda info --envs" to list the
# available environments if you forget where
# the ost-swmm environment is installed or
# named.
#
conda activate $HOME/mygit/ostswmm

#
# Setup parallelization, using SLURM if available.
#
if [ "$SLURM_CPUS_PER_TASK" != "" ]; then
  export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
elif [ "$SLURM_NPROCS" != "" ]; then
  export OMP_NUM_THREADS=$SLURM_NPROCS
fi 

#
# Launch the ostrich-swmm example and capture terminal output to a file
#
ostrich-swmm run -c model-ostrich-swmm-config.json 2>&1 | tee ostrich-swmm.stdlog
 
