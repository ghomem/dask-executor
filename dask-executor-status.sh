#!/bin/bash

# load common parameters and functions
. ./lib/dask-executor-common

check_executor_up "verbose"
rc=$?

if [ ! $rc -eq 0 ]; then
  echo "Dask executor services are not running."
else
  echo "Dask executor services are running."
fi

