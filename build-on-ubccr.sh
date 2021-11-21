#!/bin/bash
module load anaconda-python/3.8.3

conda config --set env_prompt '({name})' || exit

source activate ../pyswmm || exit

rm -Rf build

python setup.py build || exit

