import json
import argparse
from dask.distributed import Client
from collections import Counter


def get_task_state_counts(dask_scheduler):

    task_states = dict(Counter(task.state for task in dask_scheduler.tasks.values()))
    total_tasks = sum(task_states.values())
    task_states["total"] = total_tasks

    return task_states


def get_worker_tasks(dask_worker):
    return [ len(dask_worker.state.tasks), len(dask_worker.state.executing), len(dask_worker.state.has_what) ]


parser = argparse.ArgumentParser()

parser.add_argument("--verbose", help="Provide verbose output", default=False, action='store_true' )

args = parser.parse_args()

# Connect to the local Dask scheduler
dask_client = Client("tcp://127.0.0.1:8786")

dask_scheduler = dask_client.scheduler

# runs on the scheduler process
task_states = json.dumps(dask_client.run_on_scheduler(get_task_state_counts))

if args.verbose:
    scheduler_str = f"Task states in the scheduler: {task_states}"
else:
    scheduler_str = str(task_states)

print(scheduler_str)

if args.verbose:

    # runs on every worker, returns a dictionary
    worker_tasks = dask_client.run(get_worker_tasks)

    # Fetch task details from the scheduler
    scheduler_state = dask_client.scheduler_info()
    workers = scheduler_state["workers"]

    print("Worker task states:")
    for worker in workers:
        worker_id = worker

        worker_tasks_total = worker_tasks[worker][0]
        worker_tasks_executing = worker_tasks[worker][1]

        print("  *", worker_id, "tasks:", worker_tasks_total, "executing tasks:", worker_tasks_executing)

    print()
