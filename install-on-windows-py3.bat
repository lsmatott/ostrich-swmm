
REM Set installation directory
SET SRCDIR=%CD%
cd ..
rmdir /S /Q pyswmm3
SET PREFIX=%CD%\pyswmm3
cd %SRCDIR%
IF exist C:\Users\alikheir\AppData\Local\anaconda3\condabin\conda.bat (

SET PATH=%PATH%;C:\Users\alikheir\AppData\Local\anaconda3\condabin

CALL conda.bat create --prefix %PREFIX% python=3.8.3
CALL conda.bat activate %PREFIX%

pause
) ELSE (
echo "anaconda python is missing"
pause
exit
)
pip install jsonschema==2.6.0
pip install numpy
pip install swmmtoolbox==1.0.5.8
pip install Shapely==1.5

copy requirements-py3.txt requirements.txt
copy requirements-dev-py3.txt requirements-dev.txt
copy setup-py3.py setup.py
rmdir /S /Q build
python setup.py build

python setup.py install

REM Patch the swmmtoolbox (no tsutils import)
set PATCH_SRC=c:\Matott\Work\ostrich-swmm\ost-swmm-code\ostrich-swmm\swmmtoolbox.py.patch
set PATCH_DST=c:\Matott\Work\ostrich-swmm\ost-swmm-code\pyswmm3\Lib\site-packages\swmmtoolbox\swmmtoolbox.py
echo "copy %PATCH_SRC% %PATH_DST%"
copy %PATCH_SRC% %PATH_DST%

echo ""
echo "# --------------------------------------------------"
echo "To use:"
echo "  conda activate %PREFIX%"
echo "  ostrich-swmm"
echo "# --------------------------------------------------"

PAUSE

