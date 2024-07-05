#!/bin/bash

# Find the PID of the Gunicorn process and terminate it
pids=$(pgrep -f 'gunicorn')

if [ -z "$pids" ]; then
  echo "No Gunicorn process found."
else
  echo "Stopping Gunicorn process(es) with PID(s): $pids"
  kill -9 $pids
  echo "Gunicorn process(es) stopped."
fi

