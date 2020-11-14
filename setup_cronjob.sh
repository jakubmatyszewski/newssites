#!/bin/sh

# Write user's crontab to a temporary file - crontmp
crontab -l > crontmp

# Append crontmp with a new cronjob
echo "*/10 * * * * python3 $(pwd)/app.py >> $(pwd)/logs.txt" >> crontmp

# Set crontmp as a user's crontab
crontab crontmp

# Remove temporary file
rm crontmp

# Reload cron service
/etc/init.d/cron reload
