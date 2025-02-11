import json
import numpy as np
from dask.distributed import Client, wait, fire_and_forget
from flask import Flask, request
import sys

OUTPUT_DIR = "/tmp"

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


def get_task_status(dask_scheduler, key):
    for task in dask_scheduler.tasks.values():
        if task.key == key:
            return task.state

    return "not found"


# submits a calculation request
@app.route('/request_stats')
def request_stats():

    client = Client("tcp://127.0.0.1:8786")

    # submit and get a Future object, pure=False ensures key uniqueness
    future = client.submit(calc_stats, pure=False)

    # save the future key for tracking
    key = future.key

    # decouple the submitted task from this script
    fire_and_forget(future)

    results = {}

    results["key"] = key

    return json.dumps(results)


# checks whether the submitted request is ready
@app.route('/check_stats')
def check_stats():

    key = request.args.get('key')

    dask_client = Client("tcp://127.0.0.1:8786")

    dask_scheduler = dask_client.scheduler

    task_status = dask_client.run_on_scheduler(get_task_status, key=key)

    results = {}

    results["status"] = task_status

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


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
