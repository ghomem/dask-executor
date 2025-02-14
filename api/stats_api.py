import os
import sys
import json
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
from dask.distributed import Client, wait, fire_and_forget
from flask import Flask, request

OUTPUT_DIR = "/tmp"
DASK_MANAGER_URL = "tcp://127.0.0.1:8786"

# this controls how long we wait until we consider the system is busy
# it usually returns in aprox 30ms, so a timeout in the order of seconds
# means that all workers are busy processing things or that something is broken
# note: being busy is OK
PING_TIMEOUT = 2

app = Flask(__name__)


# performs some important statistics calculations
def calc_stats():
    from distributed.worker import thread_state
    key = thread_state.key

    numbers = []
    for i in range(1, 5000000):
        x = np.random.randint(0, 1000)
        numbers.append(x)

    results = {}

    results["mean"]  = np.mean(numbers)
    results["stdev"] = np.std(numbers)

    # for the sake of this demo we use OUTPUT_DIR as a database to store the results :)
    # it will be valled calc_stats_XXXXXXXXXX
    output_file = f"{OUTPUT_DIR}/{key}"

    try:
        f = open(output_file, 'w')
        f.write(json.dumps(results))
        f.close()
    except Exception as e:
        return f"could not open output file {output_file}"

    # returns a dictionary (just for testing purposes as the output is in the "database")
    return results


# simply allocates memory
def allocate_memory(factor):
    from distributed.worker import thread_state
    key = thread_state.key

    size_in_bytes = factor * 1024**3
    num_elements = int(size_in_bytes / np.float64().nbytes)  # Number of float64 elements

    array = np.full(num_elements, 1.0, dtype=np.float64)

    output_file = f"{OUTPUT_DIR}/{key}"

    # if we are here... we did not crash
    try:
        f = open(output_file, 'w')
        f.write(f"factor {factor}")
        f.close()
    except Exception as e:
        return f"could not open output file {output_file}"

    return "OK"


# gets the status of a particular task using its unique key
def get_task_status(dask_scheduler, key):
    for task in dask_scheduler.tasks.values():
        if task.key == key:
            return task.state

    return "not found"


# get state counts for tasks inside a specific worker
def get_worker_tasks(dask_worker):
    return [ len(dask_worker.state.tasks), len(dask_worker.state.executing), len(dask_worker.state.has_what) ]


# gets the overall counts of task states as stored in the dask scheduler
def get_task_state_counts(dask_scheduler):

    task_states = dict(Counter(task.state for task in dask_scheduler.tasks.values()))
    total_tasks = sum(task_states.values())

    # simplify the client logic by adding the total tasks
    task_states["total"] = total_tasks

    # simplify further the client logic ensuring that counts for some states are always present
    mandatory_states = [ "processing", "queued", "memory" ]

    for state in mandatory_states:
        if state not in task_states:
            task_states[state] = 0

    # for better user output let's ensure the dictionary is sorted
    return dict(sorted(task_states.items()))


def dask_executor_ping():

    return "pong"


# submits a calculation request
@app.route('/request_stats')
def request_stats():

    dask_client = Client(DASK_MANAGER_URL)

    # submit and get a Future object, pure=False ensures key uniqueness
    future = dask_client.submit(calc_stats, pure=False)

    # save the future key for tracking
    key = future.key

    # decouple the submitted task from this script
    fire_and_forget(future)

    results = {}

    results["key"] = key

    dask_client.close()

    return json.dumps(results)


# checks whether the submitted request is ready
@app.route('/check_stats')
def check_stats():

    results = {}

    key = request.args.get('key')

    # let's check if the task is finished
    # by checking the "database" where the result is stored
    # (in this case the filesystem at OUTPUT_DIR)
    try:
        filename = f"{OUTPUT_DIR}/{key}"
        statinfo = os.stat(filename)
        results["status"] = "finished"
        return json.dumps(results)

    except Exception as e:
        pass

    dask_client = Client(DASK_MANAGER_URL)

    dask_scheduler = dask_client.scheduler

    task_status = dask_client.run_on_scheduler(get_task_status, key=key)

    results["status"] = task_status

    dask_client.close()

    return json.dumps(results)


# downloads the calculated result
@app.route('/get_stats')
def get_stats():

    key = request.args.get('key')

    output_file = f"{OUTPUT_DIR}/{key}"

    try:
        f = open(output_file, 'r')
        results = json.load(f)
        f.close()
    except Exception as e:
        results = {}

    return json.dumps(results)


# submits a request that will allocate factor * 1GB of memory
@app.route('/request_memory')
def request_memory():

    try:
        factor = int(request.args.get('factor'))
    except Exception as e:
        factor = 1

    dask_client = Client(DASK_MANAGER_URL)

    # submit and get a Future object, pure=False ensures key uniqueness
    future = dask_client.submit(allocate_memory, factor, pure=False)

    # save the future key for tracking
    key = future.key

    # decouple the submitted task from this script
    fire_and_forget(future)

    results = {}

    results["key"] = key

    dask_client.close()

    return json.dumps(results)


# helper "ping" route to check the API responsiveness
@app.route('/check_ping')
def check_ping():

    initial_time = datetime.now()

    dask_client = Client(DASK_MANAGER_URL)

    # submit and get a Future object, pure=False ensures key uniqueness
    future = dask_client.submit(dask_executor_ping, pure=False)

    # save the future key for tracking
    key = future.key

    # wait for the execution, as this is supposed to be quick
    timeout = False
    try:
        wait([future], timeout=PING_TIMEOUT)
    except Exception as e:
        timeout = True
        pass

    results = {}

    if timeout:
        status = "busy"
    else:
        status = "free"

    dask_client.close()

    final_time = datetime.now()

    delta   = final_time - initial_time

    # calculate the latency in miliseconds, as in the usual ping command
    latency = int(delta.seconds * 1000 + delta.microseconds / 1000)

    results["status"]  = status
    results["latency"] = latency

    dask_client.close()

    return json.dumps(results)


# check the status of the execution queue
@app.route('/check_load')
def check_load():

    dask_client = Client(DASK_MANAGER_URL)

    # runs on the scheduler process
    results = dask_client.run_on_scheduler(get_task_state_counts)

    # correct counting due to dask putting an extra task inside each worker
    # rather than keeping it queued in the manager - see the comment inside dask-executor-start.sh

    # runs on every worker, returns a dictionary
    worker_tasks = dask_client.run(get_worker_tasks)

    # Fetch task details from the scheduler
    scheduler_state = dask_client.scheduler_info()
    workers = scheduler_state["workers"]

    tasks_queued_inside_workers = 0

    # get low level information from the workers
    for worker in workers:
        worker_id = worker

        worker_tasks_total     = worker_tasks[worker][0]
        worker_tasks_executing = worker_tasks[worker][1]
        worker_tasks_queued    = worker_tasks_total - worker_tasks_executing

        tasks_queued_inside_workers += worker_tasks_queued

    # correct the numbers
    results["processing"] -= tasks_queued_inside_workers
    results["queued"]     += tasks_queued_inside_workers

    dask_client.close()

    return json.dumps(results)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
