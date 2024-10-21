#!/bin/bash

if [ "$1" == "" ]; then
  PREFIX=/projects/academic/rabideau/lsmatott/pyswmm
else
  PREFIX=$1
fi

module load anaconda-python/3.8.3

conda config --set env_prompt '({name})' || exit

source activate $PREFIX || exit

cp setup-py2.py setup.py || exit
cp requirements-py2.txt requirements.txt || exit
cp requirements-dev-py2.txt requirements-dev.txt || exit

rm -Rf build

python setup.py build || exit

python setup.py install || exit

