#!/bin/bash

if [ "$1" == "" ]; then
  echo "You must specify the installation prefix."
  echo "For example: ./update-on-wsl-py3.sh ../ostswmm"
  exit
fi

PREFIX=`readlink -f $1`

conda config --set env_prompt '({name})' || exit

source activate $PREFIX || exit

cp requirements-py3.txt requirements.txt || exit
cp requirements-dev-py3.txt requirements-dev.txt || exit
cp setup-py3.py setup.py || exit
rm -Rf build || exit
python setup.py build || exit

python setup.py install || exit

