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

# Cron schedules (every 10 minutes from 6am to 11:59pm local time)
PACIFIC_SCHEDULE="*/10 6-23 * * *"
MOUNTAIN_SCHEDULE="*/10 6-23 * * *"
CENTRAL_SCHEDULE="*/10 6-23 * * *"
EASTERN_SCHEDULE="*/10 6-23 * * *"
ATLANTIC_SCHEDULE="*/10 6-23 * * *"

# Add the cron jobs to the crontab
(crontab -l 2>/dev/null; echo "$PACIFIC_SCHEDULE $PACIFIC_CMD"; echo "$MOUNTAIN_SCHEDULE $MOUNTAIN_CMD"; echo "$CENTRAL_SCHEDULE $CENTRAL_CMD"; echo "$EASTERN_SCHEDULE $EASTERN_CMD"; echo "$ATLANTIC_SCHEDULE $ATLANTIC_CMD") | crontab -

echo "Cron jobs created successfully."
echo "To view the cron jobs, run: crontab -l"
echo "To edit the cron jobs, run: crontab -e"
