#!/bin/bash

# Activate the python environment
eval "$(conda shell.bash hook)"
conda activate pyswmm

# Delete report file 
rm -f lid_model.rpt

# Launch ostrich-swmm
ostrich-swmm run -c ./ostrich-swmm-config.json

