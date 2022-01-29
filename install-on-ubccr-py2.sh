#!/bin/bash

if [ "$1" == "" ]; then
  echo "You must specify the installation prefix,"
  exit
fi

PREFIX=$1

module load anaconda-python/3.8.3

conda create --prefix $PREFIX python=2.7 || exit

conda config --set env_prompt '({name})' || exit

source activate $PREFIX || exit

pip install docutils==0.13.1 || exit
pip install jsonschema==2.6.0 || exit
pip install numpy==1.12 || exit
conda install regex || exit
pip install swmmtoolbox==1.0.5.8 || exit
pip install Shapely==1.5 || exit

cp requirements-py2.txt requirements.txt || exit
cp requirements-dev-py2.txt requirements-dev.txt || exit
cp setup-py2.py setup.py || exit

python setup.py install || exit

echo ""
echo "# --------------------------------------------------"
echo "To use:"
echo "  module use /projects/academic/rabideau/modulefiles"
echo "  module load ostrich-swmm"
echo "  ostrich-swmm"
echo "# --------------------------------------------------"

