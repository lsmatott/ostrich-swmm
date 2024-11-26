
REM Set installation directory
SET SRCDIR=%CD%
cd ..
rmdir -p pyswmm3
SET PREFIX=%CD%\pyswmm3
cd %SRCDIR%

conda create -p %PREFIX%

conda activate %PREFIX%

copy requirements-py3.txt requirements.txt
copy requirements-dev-py3.txt requirements-dev.txt
copy setup-py3.py setup.py

rmdir -p build

python setup.py build

PAUSE
