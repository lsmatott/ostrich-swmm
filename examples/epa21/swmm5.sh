#!/bin/bash

export PATH=/path/to/swmm5/1.0.15/bin:$PATH
export LD_LIBRARY_PATH=/path/to/swmm5/1.0.15/bin:$LD_LIBRARY_PATH

swmm5 "$@"
