# Introduction

WARNING: experimental code

This is an experiment with Dask as an assynchronous background executor for a web API.

In this example we use Flask to implement an API, that calculates the mean and stdev of a list of 5M randomly generated numbers between 0 and 1000.

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

Test task submission via cli
```
python3 tests/local/test-submit-tasks.py
```

Check tasks
```
./control-scripts/dask-executor-check-tasks.py
```

Request a task via API and get the task ID
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
