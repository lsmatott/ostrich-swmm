#!/bin/bash

if [ "$1" == "" ]; then
  echo "You must specify the installation prefix."
  echo "For example: ./install-on-wsl-py3.sh ../ostswmm"
  exit
fi

PREFIX=`readlink -f $1`

conda create --prefix $PREFIX python=3.8.3 || exit

conda config --set env_prompt '({name})' || exit

source activate $PREFIX || exit

pip install jsonschema==2.6.0 || exit
pip install numpy || exit
pip install swmmtoolbox==1.0.5.8 || exit
pip install Shapely==1.5 || exit
conda install geos==3.9.1 || exit

cp requirements-py3.txt requirements.txt || exit
cp requirements-dev-py3.txt requirements-dev.txt || exit
cp setup-py3.py setup.py || exit
rm -Rf build || exit
python setup.py build || exit

python setup.py install || exit

# patch the swmmtoolbox
sed -i 's/from tstoolbox import tsutils/# from tstoolbox import tsutils/g'  $PREFIX/lib/python3.8/site-packages/swmmtoolbox/swmmtoolbox.py

# list the environment
conda info --envs || exit
