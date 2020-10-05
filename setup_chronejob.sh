#!/bin/sh

crontab -l > crontmp

echo "0 * * * * python3 $(pwd)/app.py >> $(pwd)/logs.txt" >> crontmp

crontab crontmp
rm crontmp
