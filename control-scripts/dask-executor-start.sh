#!/bin/bash

# load common parameters and functions
. ./lib/dask-executor-common

check_executor_up
rc=$?

if [ $rc -eq 0 ]; then
  echo "Dask executor services are already running. Exiting."
  exit 1
fi

echo "Starting dask executor with $NUM_WORKERS workers and $MEMORY_LIMIT memory limit."

# Start the Dask scheduler explicitly on 127.0.0.1
dask-scheduler --host 127.0.0.1 --port 8786 &>> $LOG_FILE &
echo "Dask scheduler started..."

# Give the scheduler some time to start
sleep $WAIT_TIME_SCHEDULER

dask-worker tcp://127.0.0.1:8786 --memory-limit $MEMORY_LIMIT --nworkers $NUM_WORKERS --nthreads 1 &>> $LOG_FILE &
echo "Dask workers started..."

# FIXME use gunicorn
python3 ./api/stats_api.py 2>1 &>> $LOG_FILE &
echo "API started..."

echo "All done."

