#!/bin/bash

# load common parameters and functions
. ./lib/dask-executor-common

check_executor_up
rc=$?

if [ $rc -eq 0 ]; then
  echo "Dask executor services are already running. Exiting."
  exit 1
fi

if [ ! -z $ENV_NUM_WORKERS ]; then
  num_workers=$ENV_NUM_WORKERS
else
  num_workers=$NUM_WORKERS
fi

if [ ! -z $ENV_MEMORY_LIMIT ]; then
  memory_limit=$ENV_MEMORY_LIMIT
else
  memory_limit=$MEMORY_LIMIT
fi

echo "Starting dask executor with $num_workers workers and $memory_limit memory limit."

# Start the Dask scheduler explicitly on 127.0.0.1
dask-scheduler --host 127.0.0.1 --port 8786 &>> $LOG_FILE &
echo "Dask scheduler started..."

# Give the scheduler some time to start
sleep $WAIT_TIME_SCHEDULER

dask-worker tcp://127.0.0.1:8786 --memory-limit $memory_limit --nworkers $num_workers --nthreads 1 &>> $LOG_FILE &
echo "Dask workers started..."

# FIXME use gunicorn
python3 ./api/stats_api.py &>> $LOG_FILE &
echo "API started..."

echo "All done."

