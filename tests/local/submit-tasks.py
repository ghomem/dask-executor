import time
import numpy as np
from dask.distributed import Client, wait, fire_and_forget

NR_TASKS = 20
DELAY = 20
OUTPUT_DIR = "/tmp"


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
client = Client("tcp://127.0.0.1:8786")

futures = []

for j in range(1, NR_TASKS + 1):

    # submit and get a Future object
    future = client.submit(heavy_hello_world, j)

    # print the future key for tracking
    print(f"Task {j} submitted with key: {future.key}")

    # decouple the submitted task from this script
    fire_and_forget(future)

print()
print(f"Check the output at {OUTPUT_DIR}/heavy_hello_world_*")
