from dask.distributed import Client
from collections import Counter

def get_task_state_counts(dask_scheduler):
    return dict(Counter(task.state for task in dask_scheduler.tasks.values()))

def get_worker_tasks(dask_worker):
    return [ len(dask_worker.state.tasks), len(dask_worker.state.executing), len(dask_worker.state.has_what) ]

# Connect to the local Dask scheduler
dask_client = Client("tcp://127.0.0.1:8786")

dask_scheduler = dask_client.scheduler

# runs on the scheduler process
task_states = dask_client.run_on_scheduler(get_task_state_counts)
print(f"Task states in the scheduler: {task_states}")

# runs on every worker, returns a dictionary
worker_tasks = dask_client.run(get_worker_tasks)

# this is a debug message that I am using the check various fields from the worker
print("\ndebug:", worker_tasks, "\n")

# Fetch task details from the scheduler
scheduler_state = dask_client.scheduler_info()
workers = scheduler_state["workers"]

print("Worker task states:")
for worker in workers:
    worker_id = worker
    worker_task_count = scheduler_state["workers"][worker]["metrics"]["task_counts"]

    try:
        # strange as it may seem when the worker is busy the task_count is { "cancelled": 1" }
        # and otherwise it is empty
        worker_status = worker_task_count["cancelled"]
        worker_status_str = "busy"
    except Exception as e:
        worker_status_str = "idle"

    worker_tasks_total = worker_tasks[worker][0]
    worker_tasks_executing = worker_tasks[worker][1]

    print("  *", worker_id, "tasks:", worker_tasks_total, "executing tasks:", worker_tasks_executing, "status:", worker_status_str)

print()
