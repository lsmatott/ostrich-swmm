#!/bin/bash
module load intel/15.0
export PATH=/util/academic/swmm/5.1.010/bin:$PATH
export PATH=/projects/academic/zhenduoz/kmmacro/ostrich-swmm/bin:$PATH
if [ "$SLURM_CPUS_PER_TASK" != "" ]; then

  export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

elif [ "$SLURM_NPROCS" != "" ]; then

  export OMP_NUM_THREADS=$SLURM_NPROCS

else

  export OMP_NUM_THREADS=6
fi 
ostrich-swmm run -c model-ostrich-swmm-config.json
 
