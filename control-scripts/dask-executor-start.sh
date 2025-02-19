#!/bin/bash

# load common parameters and functions
. ./lib/dask-executor-common

check_executor_up
rc=$?

if [ $rc -eq 0 ]; then
  echo "Dask executor services are already running. Exiting."
  exit 1
fi

# we respect the externally supplied values,
# falling back to the default ones if necessary
if [ ! -z $ENV_NUM_WORKERS ]; then
  NUM_WORKERS=$ENV_NUM_WORKERS
else
  NUM_WORKERS=$NUM_WORKERS
fi

if [ ! -z $ENV_MEMORY_LIMIT ]; then
  MEMORY_LIMIT=$ENV_MEMORY_LIMIT
else
  MEMORY_LIMIT=$MEMORY_LIMIT
fi

# whether they are defaults or values from the outside
# these variables are always exported
export NUM_WORKERS
export MEMORY_LIMIT

cd api
./start.sh &>> $LOG_FILE &
echo "Dask executor started..."

echo "All done."

