import time
import argparse
import numpy as np
from dask.distributed import Client, wait, fire_and_forget

DELAY = 20
OUTPUT_DIR = "/tmp"


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


# dummy execution function
# takes about 15s in the test env
def heavy_hello_world(n):

    # we write to a file just so that we can confirm the execution is right
    # (for the sake of a PoC of course)
    output_file = f"{OUTPUT_DIR}/heavy_hello_world_{n}"

    try:
        f = open(output_file, 'w')
    except Exception as e:
        return f"could not open output file {output_file}"

    for i in range(1, 5000000):
        x = np.random.randint(0, 1000)
        f.write(str(x) + '\n')

    f.close()

    return f"Finished task {n}"


# main script


parser = argparse.ArgumentParser(description='Test local task submission')

parser.add_argument("n", help='Number of tasks to submit', type=int, nargs='?', default=5)

args = parser.parse_args()

dask_client = Client("tcp://127.0.0.1:8786")

futures = []

for j in range(1, args.n + 1):

    # submit and get a Future object, pure=False ensures key uniqueness
    future = dask_client.submit(calc_stats, pure=False)

    # print the future key for tracking
    print(f"Task {j} submitted with key: {future.key}")

    # decouple the submitted task from this script
    fire_and_forget(future)

dask_client.close()

print()
print(f"Check the output at: {OUTPUT_DIR}/calc_stats_*")
print()
print("Check the task status with:")
print("python3 control-scripts/dask-executor-check-tasks.py")
print()
