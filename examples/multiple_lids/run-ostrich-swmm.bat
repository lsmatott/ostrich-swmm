@echo on

REM Activate the python environment
set PREFIX=pyswmm
CALL conda.bat activate %PREFIX%

REM Delete report file 
DEL /Q lid_model.rpt

REM Launch ostrich-swmm
ostrich-swmm run -c ./ostrich-swmm-config.json

REM pause
