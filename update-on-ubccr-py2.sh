#!/bin/bash

PREFIX=/projects/academic/rabideau/lsmatott/pyswmm

module load anaconda-python/3.8.3

conda config --set env_prompt '({name})' || exit

source activate $PREFIX || exit

cp setup-py2.py setup.py || exit
cp requirements-py2.txt requirements.txt || exit
cp requirements-dev-py2.txt requirements-dev.txt || exit

rm -Rf build

python setup.py build || exit

python setup.py install || exit

