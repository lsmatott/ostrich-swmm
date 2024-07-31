@echo on

REM Activate the python environment
set PREFIX=C:\Matott\Work\ostrich-swmm\ost-swmm-code\pyswmm3
CALL conda.bat activate %PREFIX%

REM Delete report file 
DEL /Q lid_model.rpt

REM Launch ostrich-swmm
ostrich-swmm run -c ./ostrich-swmm-config.json

REM pause
