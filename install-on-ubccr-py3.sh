#!/bin/bash

if [ "$1" == "" ]; then
  echo "You must specify the installation prefix,"
  exit
fi

PREFIX=$1

module load anaconda-python/3.8.3
(mkdir $PREFIX && cd $PREFIX) || cd $PREFIX
conda create --name pyswmm python=3.8.3 || exit

source activate pyswmm || exit

pip install jsonschema==2.6.0 || exit
pip install numpy || exit
pip install swmmtoolbox==4.0.14 || exit
pip install Shapely==1.8.5 || exit

cd ..
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

