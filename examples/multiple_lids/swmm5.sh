#!/bin/bash

export PATH=/mnt/c/Matott/Work/ostrich-swmm/swmm5/1.0.15/bin:$PATH
export LD_LIBRARY_PATH=/mnt/c/Matott/Work/ostrich-swmm/swmm5/1.0.15/bin:$LD_LIBRARY_PATH

swmm5 lid_model.inp lid_model.rpt lid_model.out 
