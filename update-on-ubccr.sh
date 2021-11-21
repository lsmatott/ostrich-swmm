#!/bin/bash

PREFIX=/projects/academic/rabideau/lsmatott/pyswmm

module load anaconda-python/3.8.3

conda config --set env_prompt '({name})' || exit

source activate $PREFIX || exit

rm -Rf build

python setup.py build || exit

python setup.py install || exit

