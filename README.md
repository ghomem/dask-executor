# Introduction

WARNING: experimental code

This is an experiment with Dask as an assynchronous background executor for a web API.

In this example we use Flask to implement an API that calculates the mean and stdev of a list of 5M randomly generated numbers between 0 and 1000.

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

# Docker notes

Build the image locally
```
sudo docker build -t dask-executor:latest .
```

Launch a container from the local image
```
sudo docker run -d -p 8080:5000 dask-executor /bin/bash
```
