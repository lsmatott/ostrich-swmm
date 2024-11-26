#!/bin/bash

if [ "$1" == "" ]; then
  PREFIX=../py3swmm
else
  PREFIX=$1
fi

module load anaconda-python/3.8.3

conda config --set env_prompt '({name})' || exit

source activate $PREFIX || exit

cp requirements-py3.txt requirements.txt || exit
cp requirements-dev-py3.txt requirements-dev.txt || exit
cp setup-py3.py setup.py || exit

rm -Rf build

python setup.py build || exit

