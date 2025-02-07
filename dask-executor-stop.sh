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

pkill dask-scheduler &>/dev/null
sleep $WAIT_FOR_PROCESS
pkill -9 dask-scheduler &>/dev/null
sleep $WAIT_FOR_PROCESS

pkill dask-worker &>/dev/null
sleep $WAIT_FOR_PROCESS
pkill -9 dask-worker &>/dev/null
sleep $WAIT_FOR_PROCESS

check_executor_up "verbose"
rc=$?

if [ ! $rc -eq 0 ]; then
  echo "All done."
else
  echo "Error: dask processes are still running"
fi

