# Introduction

WARNING: experimental code

This is an experiment with Dask as an assynchronous background executor for a web API.

In this example we use Flask to implement an API that calculates the mean and stdev of a list of 5M randomly generated numbers between 0 and 1000.

These are the available endpoints:

* request_stats - requests the execution of a calculation task
* check_stats - checks the status of a task
* get_stats - returns the execution results, if they are available
* check_ping - executes a unitary task and returns the latency in miliseconds
* check load - returns the counts of dask tasks for each state (processing, queued, etc)

We also implemented an endpoint that demos the dask memory control:

* request_memory

# Operation

Install dask
```
sudo apt install python3-dask python3-flask
```

Start services
```
./control-scripts/dask-executor-start.sh
```

Stop services

```
./control-scripts/dask-executor-stop.sh
```

Check services
```
./control-scripts/dask-executor-status.sh
```

Test multiple task submission via cli (10 tasks in the example)
```
python3 tests/local/test-submit-tasks.py 10
```

Check tasks
```
./control-scripts/dask-executor-check-tasks.py
```

Submit a task via API and get the task ID
```
curl localhost:5000/request_stats
```

Check status of a task by ID, via API
```
curl localhost:5000/check_stats?key=calc_stats-2e9cd200-f24d-43da-bb8b-b14d3dcb314e
```

Download the task result via API
```
curl localhost:5000/get_stats?key=calc_stats-2e9cd200-f24d-43da-bb8b-b14d3dcb314e
```

Test submit / check / download process via API (10 tasks in the example)
```
python3 tests/api/test-submit-tasks.py -H localhost:5000 -ns -np 10
```

Allocate 1G of memory in a task (this will work):
```
curl http://localhost:5000/request_memory?factor=1
```

Allocate 2G of memory in a task (this will fail since the limit is 2G):
```
curl http://localhost:5000/request_memory?factor=2
```

Check whether a memory allocation task resulted in state "finished" or "not found":
```
curl localhost:5000/check_stats?key=allocate_memory-7768a58e-6958-4d61-a5eb-dc3e9e4d7a09
```

# Docker notes

Build the image locally
```
sudo docker build -t dask-executor:latest .
```

Launch a container from the local image
```
sudo docker run -d -p 8080:5000 dask-executor /bin/bash
```
