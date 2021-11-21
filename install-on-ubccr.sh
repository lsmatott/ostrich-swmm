#!/bin/bash
module load anaconda-python/3.8.3

conda create --prefix ../pyswmm python=2.7 || exit

conda config --set env_prompt '({name})' || exit

source activate ../pyswmm || exit

pip install jsonschema==2.6.0 || exit
pip install numpy==1.12 || exit
pip install swmmtoolbox==1.0.5.8 || exit
pip install Shapely==1.5 || exit

python setup.py install || exit

# --------------------------------------------------
# To use:
# module load anaconda-python/3.8.3
# module load geos/3.9.0
# conda config --set env_prompt '({name})'
# source activate /path/to/pyswmm
# ostrich-swmm
# --------------------------------------------------

