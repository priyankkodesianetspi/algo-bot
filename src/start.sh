#!/bin/bash

# Navigate to your Flask application directory
cd ~/algo-bot/src

source ~/algo-bot/bin/activate

# Run the Flask application using Gunicorn
nohup gunicorn --workers 3 --bind 127.0.0.1:8000 app:app > gunicorn.log 2>&1 &

echo "Gunicorn started. Check gunicorn.log for details."

