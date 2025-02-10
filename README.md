WARNING: experimental code

Install dask
```
sudo apt install python3-dask
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

Submit tasks
```
python3 tests/local/test-submit-tasks.py
```

Check tasks
```
./control-scripts/dask-executor-check-tasks.py
```
