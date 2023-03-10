@echo off

copy ostIn_parallel.txt ostIn.txt

REM mpiexec location: C:\Program Files\Microsoft MPI\Bin

REM replace C:\bin with location of OSTRICH installation
mpiexec -n 4 C:\Matott\Work\ostrich-swmm\Ostrich\bin\OstrichMPI.exe

pause
