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

# Worker saturation defaults to 1.1, which in theory would explain the behaviour we see, i.e.,
# that each worker is receiving two tasks at once, if there are more tasks then workers.
#
# https://distributed.dask.org/en/stable/scheduling-policies.html#id2
#
# But turns our that, while setting it to higher values increases the pending tasks in the workers
# (i.e decreases the queued tasks in the scheduler... putting them to wait directly in the workder)
# lowering it to 1.0 does not make any difference, i.e, when we have many tasks each worker always has
# one running task and one pending task. This can be seen by launching, for example, 10 tasks and then running
#
# python3 ../control-scripts/dask-executor-check-tasks.py --verbose
#
# In practice, this does not cause much harm because when we have less tasks than workers there is no queueing in the workers
# i.e. some workers have a running task and some workers are idle. The harm that it causes is miscounting the number of tasks
# in state "processing" and in state "queued" since the ones waiting inside the workers are counted as "processing".
#
# This is fixed in the python code by correcting the counters. I leave this variable here commented for future reference
#
#export DASK_DISTRIBUTED__SCHEDULER__WORKER_SATURATION=1.0

# Start the Dask scheduler explicitly on 127.0.0.1
dask-scheduler --host 127.0.0.1 --port 8786 &>> $LOG_FILE &
echo "Dask scheduler started..."

# check the worker saturation value, for awareness
dask config list | grep saturation

# Give the scheduler some time to start
sleep $WAIT_TIME_SCHEDULER

dask-worker tcp://127.0.0.1:8786 --memory-limit $memory_limit --nworkers $num_workers --nthreads 1 &>> $LOG_FILE &
echo "Dask workers started..."

# FIXME use gunicorn
python3 ./api/stats_api.py &>> $LOG_FILE &
echo "API started..."

echo "All done."

