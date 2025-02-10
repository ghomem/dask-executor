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
python3 tests/local/submit-tasks.py
```

Check tasks
```
./control-scripts/check-tasks.py
```
