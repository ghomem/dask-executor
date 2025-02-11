#!/bin/bash

# load common parameters and functions
. ./lib/dask-executor-common

check_executor_up "verbose"
rc=$?

if [ ! $rc -eq 0 ]; then
  echo "Dask executor services are not running. Exiting"
  exit $E_ERR
else
  echo "Stopping dask executor services..."
fi

kill_service dask-scheduler
kill_service dask-worker
kill_service "python3 ./api/stats_api.py" XXX

check_executor_up "verbose"
rc=$?

if [ ! $rc -eq 0 ]; then
  echo "All done."
else
  echo "Error: dask processes are still running"
fi

