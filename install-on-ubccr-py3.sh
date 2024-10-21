#!/bin/bash

if [ "$1" == "" ]; then
  echo "You must specify the installation prefix,"
  exit
fi

PREFIX=$1

module load anaconda-python/3.8

conda create --prefix $PREFIX python=3.8 || exit

conda config --set env_prompt '({name})' || exit

source activate $PREFIX || exit

pip install jsonschema==2.6.0 || exit
pip install numpy || exit
pip install swmmtoolbox==4.0.14 || exit
pip install Shapely==1.8.5 || exit

cp requirements-py3.txt requirements.txt || exit
cp requirements-dev-py3.txt requirements-dev.txt || exit
cp setup-py3.py setup.py || exit
rm -Rf build || exit
python setup.py build || exit

python setup.py install || exit

echo ""
echo "# --------------------------------------------------"
echo "To use:"
echo "  module use /projects/academic/rabideau/modulefiles"
echo "  module load ostrich-swmm-py3"
echo "  ostrich-swmm"
echo "# --------------------------------------------------"

