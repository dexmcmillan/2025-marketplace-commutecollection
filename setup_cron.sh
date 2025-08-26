#!/bin/bash

# This script sets up cron jobs to run the timezone-specific python scripts.

# The directory where this script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# The directory where the scripts are located (one level up from this script's location)
APP_DIR=$(dirname "$SCRIPT_DIR/2025-marketplace-commutecollection")

# The python executable path (assuming a uv venv in the project)
PYTHON_EXECUTABLE="$APP_DIR/.venv/bin/python"

# Log file
LOG_FILE="$APP_DIR/cron.log"

# Cron job commands
PACIFIC_CMD="cd $APP_DIR && $PYTHON_EXECUTABLE $APP_DIR/scripts_by_timezone/pacific.py >> $LOG_FILE 2>&1"
MOUNTAIN_CMD="cd $APP_DIR && $PYTHON_EXECUTABLE $APP_DIR/scripts_by_timezone/mountain.py >> $LOG_FILE 2>&1"
CENTRAL_CMD="cd $APP_DIR && $PYTHON_EXECUTABLE $APP_DIR/scripts_by_timezone/central.py >> $LOG_FILE 2>&1"
EASTERN_CMD="cd $APP_DIR && $PYTHON_EXECUTABLE $APP_DIR/scripts_by_timezone/eastern.py >> $LOG_FILE 2>&1"
ATLANTIC_CMD="cd $APP_DIR && $PYTHON_EXECUTABLE $APP_DIR/scripts_by_timezone/atlantic.py >> $LOG_FILE 2>&1"

# Cron schedules (every 10 minutes from 6am to 11:59pm local time, converted to UTC)
PACIFIC_SCHEDULE="*/10 13-23,0-6 * * *"   # UTC-7: 6am-11:59pm is 13:00-06:59 UTC
MOUNTAIN_SCHEDULE="*/10 12-23,0-5 * * *"  # UTC-6: 6am-11:59pm is 12:00-05:59 UTC
CENTRAL_SCHEDULE="*/10 11-23,0-4 * * *" # UTC-5: 6am-11:59pm is 11:00-04:59 UTC
EASTERN_SCHEDULE="*/10 10-23,0-3 * * *"  # UTC-4: 6am-11:59pm is 10:00-03:59 UTC
ATLANTIC_SCHEDULE="*/10 9-23,0-2 * * *" # UTC-3: 6am-11:59pm is 09:00-02:59 UTC

# Add the cron jobs to the crontab
(crontab -l 2>/dev/null; echo "$PACIFIC_SCHEDULE $PACIFIC_CMD"; echo "$MOUNTAIN_SCHEDULE $MOUNTAIN_CMD"; echo "$CENTRAL_SCHEDULE $CENTRAL_CMD"; echo "$EASTERN_SCHEDULE $EASTERN_CMD"; echo "$ATLANTIC_SCHEDULE $ATLANTIC_CMD") | crontab -

echo "Cron jobs created successfully."
echo "To view the cron jobs, run: crontab -l"
echo "To edit the cron jobs, run: crontab -e"
