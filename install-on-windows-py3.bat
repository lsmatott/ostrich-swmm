
REM Set installation directory
SET SRCDIR=%CD%
cd ..
rmdir /S /Q pyswmm3
SET PREFIX=%CD%\pyswmm3
cd %SRCDIR%\pyswmm3

CALL conda create --name pyswmm python=3.8.3
CALL conda activate pyswmm

pip install jsonschema==2.6.0
pip install numpy
pip install swmmtoolbox==4.0.14
pip install shapely==1.8.5

cd %SRCDIR%
copy requirements-py3.txt requirements.txt
copy requirements-dev-py3.txt requirements-dev.txt
copy setup-py3.py setup.py
rmdir /S /Q build
python setup.py build

python setup.py install

echo ""
echo "# --------------------------------------------------"
echo "To use:"
echo "  conda activate %PREFIX%"
echo "  ostrich-swmm"
echo "# --------------------------------------------------"

PAUSE

