#!/bin/bash

# This script sets up cron jobs to run the timezone-specific python scripts.

# The user's home directory
HOME_DIR=$(eval echo ~$USER)

# The directory where the scripts are located
APP_DIR="$HOME_DIR/scripts_by_timezone"

# The python executable path
PYTHON_EXECUTABLE=$(which python3)

# Cron job commands
PACIFIC_CMD="cd $HOME_DIR && $PYTHON_EXECUTABLE $APP_DIR/pacific.py"
MOUNTAIN_CMD="cd $HOME_DIR && $PYTHON_EXECUTABLE $APP_DIR/mountain.py"
CENTRAL_CMD="cd $HOME_DIR && $PYTHON_EXECUTABLE $APP_DIR/central.py"
EASTERN_CMD="cd $HOME_DIR && $PYTHON_EXECUTABLE $APP_DIR/eastern.py"
ATLANTIC_CMD="cd $HOME_DIR && $PYTHON_EXECUTABLE $APP_DIR/atlantic.py"

# Cron schedules (every 10 minutes during specified UTC hours)
# Local times: 2-4am, 8-10am, 5-7pm
PACIFIC_SCHEDULE="*/10 0,1,9,10,15,16 * * *"   # UTC-7: 9-11, 15-17, 0-2 UTC
MOUNTAIN_SCHEDULE="*/10 0,8,9,14,15,23 * * *"  # UTC-6: 8-10, 14-16, 23-1 UTC
CENTRAL_SCHEDULE="*/10 0,7,8,13,14,22,23 * * *" # UTC-5: 7-9, 13-15, 22-0 UTC
EASTERN_SCHEDULE="*/10 6,7,12,13,21,22 * * *"  # UTC-4: 6-8, 12-14, 21-23 UTC
ATLANTIC_SCHEDULE="*/10 5,6,11,12,20,21 * * *" # UTC-3: 5-7, 11-13, 20-22 UTC

# Add the cron jobs to the crontab
(crontab -l 2>/dev/null; echo "$PACIFIC_SCHEDULE $PACIFIC_CMD"; echo "$MOUNTAIN_SCHEDULE $MOUNTAIN_CMD"; echo "$CENTRAL_SCHEDULE $CENTRAL_CMD"; echo "$EASTERN_SCHEDULE $EASTERN_CMD"; echo "$ATLANTIC_SCHEDULE $ATLANTIC_CMD") | crontab -

echo "Cron jobs created successfully."
echo "To view the cron jobs, run: crontab -l"
echo "To edit the cron jobs, run: crontab -e"
