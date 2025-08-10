#!/bin/bash

# Start cron daemon (Docker-compatible way)
echo "Starting cron daemon..."
cron

# Wait a moment for cron to start
sleep 2

# Check if cron is running
if pgrep cron > /dev/null; then
    echo "Cron daemon started successfully"
    echo "Scheduled jobs:"
    crontab -l
else
    echo "Warning: Cron daemon failed to start"
fi

# Start the main application in background
echo "Starting main application..."
python main.py &

# Keep container alive and monitor processes
echo "Container is running. Monitoring processes..."
while true; do
    # Check if main.py is still running
    if ! pgrep -f "python main.py" > /dev/null; then
        echo "Warning: main.py process stopped"
    fi
    
    # Check if cron is still running
    if ! pgrep cron > /dev/null; then
        echo "Warning: Cron daemon stopped, restarting..."
        cron
    fi
    
    sleep 30
done 