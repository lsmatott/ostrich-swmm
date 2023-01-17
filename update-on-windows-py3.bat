
REM Set installation directory
SET SRCDIR=%CD%
cd ..
SET PREFIX=%CD%\pyswmm3
cd %SRCDIR%

CALL conda.bat activate %PREFIX%

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

