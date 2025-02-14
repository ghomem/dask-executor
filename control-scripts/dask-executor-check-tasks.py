import json
import argparse
from dask.distributed import Client
from collections import Counter


def get_task_state_counts(dask_scheduler):

    task_states = dict(Counter(task.state for task in dask_scheduler.tasks.values()))
    total_tasks = sum(task_states.values())
    task_states["total"] = total_tasks

    # simplify further the client logic ensuring that counts for some states are always present
    mandatory_states = [ "processing", "queued", "memory" ]

    for state in mandatory_states:
        if state not in task_states:
            task_states[state] = 0


    return dict(sorted(task_states.items()))


def get_worker_tasks(dask_worker):
    return [ len(dask_worker.state.tasks), len(dask_worker.state.executing), len(dask_worker.state.has_what) ]


parser = argparse.ArgumentParser()

parser.add_argument("--verbose", help="Provide verbose output", default=False, action='store_true' )

args = parser.parse_args()

# Connect to the local Dask scheduler
dask_client = Client("tcp://127.0.0.1:8786")

dask_scheduler = dask_client.scheduler

# runs on the scheduler process
task_states = dask_client.run_on_scheduler(get_task_state_counts)
task_states_corrected = task_states.copy()

# runs on every worker, returns a dictionary
worker_tasks = dask_client.run(get_worker_tasks)

# Fetch task details from the scheduler
scheduler_state = dask_client.scheduler_info()
workers = scheduler_state["workers"]

tasks_queued_inside_workers = 0

for worker in workers:

    worker_tasks_total     = worker_tasks[worker][0]
    worker_tasks_executing = worker_tasks[worker][1]
    worker_tasks_queued    = worker_tasks_total - worker_tasks_executing

    tasks_queued_inside_workers += worker_tasks_queued

# correct the numbers
task_states_corrected["processing"] -= tasks_queued_inside_workers
task_states_corrected["queued"]     += tasks_queued_inside_workers

json_task_states = json.dumps(task_states)
json_task_states_corrected = json.dumps(task_states_corrected)

if args.verbose:
    scheduler_str = f"Task states in the scheduler: {json_task_states}"
    scheduler_str_corrected = f"Task states in the scheduler: {json_task_states_corrected} (corrected)"
else:
    scheduler_str = json_task_states
    scheduler_str_corrected = f"{json_task_states_corrected} (corrected)"

print(scheduler_str)
print(scheduler_str_corrected)

if args.verbose:
    print()
    print("Worker task states:")
    for worker in workers:

        print("  *", worker, "tasks:", worker_tasks_total, "executing tasks:", worker_tasks_executing)

    print()

dask_client.close()
