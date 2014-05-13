#!/bin/bash

# create the log file
mkdir -p logs
logfile="logs/log_$(date +"%F_%T").txt"

# run in the backroung if requested, always writing to log
if [ "$1" == "--background" ]
then
	python3 -u run.py > $logfile &
    echo "$!" > .pid.temp
# force kill the program if it is running
elif [ "$1" == "--kill" ]
then
    # only kill if pid file exists
    if [ -e ".pid.temp" ]
    then
        # kills the process and all children
        pid=`cat .pid.temp`
        kill -- -$pid
        rm .pid.temp
    else
        echo "No PID file detected!"
    fi
else
    # can't get the python3 process, so get the script process
    # kill will kill all children, so it will still work
    echo "$$" > .pid.temp
	python3 -u run.py | tee $logfile
    # if the program is manually terminated, remove the .pid file
    rm .pid.temp
fi

