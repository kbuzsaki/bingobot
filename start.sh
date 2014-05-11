#!/bin/bash

# create the log filE
mkdir -p logs
logfile="logs/log_$(date +"%F_%T").txt"

# run in the backroung if requested, always writing to log
if [ "$1" == "--background" ]
then
	python3 -u run.py > $logfile &
else
	python3 -u run.py | tee $logfile
fi

