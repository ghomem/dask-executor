import time
import numpy as np
from dask.distributed import Client, wait

NR_TASKS=1000
DELAY=20
OUTPUT_DIR="/tmp"

# dummy function
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
        x=np.random.randint(0,1000)
        f.write(str(x) + '\n')

    f.close()

    return f"Finished task {n}"

client = Client("tcp://127.0.0.1:8786")

futures = []

for j in range(1,NR_TASKS):
    # Submit and get a Future object
    future = client.submit(heavy_hello_world, j)
    futures.append(future)

    # Print the future key for tracking
    print(f"Task {j} submitted with key: {future.key}")

print("Waiting for completion...")

# we need to wait here or all but the first X tasks are lost
# X is the number of workers
wait(futures)

print()
print(f"Check the output at {OUTPUT_DIR}/heavy_hello_world_*")
