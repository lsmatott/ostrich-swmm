
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

REM delete the egg to ensure installation
DEL C:\Matott\Work\ostrich-swmm\ost-swmm-code\pyswmm3\Lib\site-packages\ostrich_swmm*.egg

python setup.py install

echo ""
echo "# --------------------------------------------------"
echo "To use:"
echo "  conda activate %PREFIX%"
echo "  ostrich-swmm"
echo "# --------------------------------------------------"

pause
