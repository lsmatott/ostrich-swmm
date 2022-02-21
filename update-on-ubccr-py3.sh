#!/bin/bash

if [ "$1" == "" ]; then
  PREFIX=/projects/academic/rabideau/lsmatott/py3swmm
else
  PREFIX=$1
fi

module use /projects/academic/rabideau/modulefiles
module load anaconda-python

conda config --set env_prompt '({name})' || exit

source activate $PREFIX || exit

cp setup-py3.py setup.py || exit
cp requirements-py3.txt requirements.txt || exit
cp requirements-dev-py3.txt requirements-dev.txt || exit

rm -Rf build

python setup.py build || exit

python setup.py install || exit

