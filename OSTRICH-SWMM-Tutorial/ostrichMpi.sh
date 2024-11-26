#!/bin/bash

#
# Optional: load necessary modules
#
noModules=`type module 2>&1 | grep "not found" | wc -l`
if [ "$noModules" == "0" ]; then
  echo "Loading modules ..."
  module load ostrich
fi

#
# Optional: setup PATH variable
#
# Hint: adjust the path below to match where
# Ostrich and OstrichMpi are installed.
#
if [ "$noModules" == "1" ]; then
  echo "Setting paths ..."
  export PATH=$HOME/mygit/ostrich/bin:$PATH
fi

#
# Launch ostrich
#
rm -Rf mod[0-9]
mpirun -np 5 OstrichMpi 2>&1 | tee OstrichMpi.stdout

 
