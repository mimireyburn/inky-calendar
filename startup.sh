#!/bin/bash

# Wait for internet connection
while ! ping -c 1 -W 1 google.com; do
    sleep 1
done

# Navigate to your folder
cd /home/calendar/inky-calendar

# Git pull
git pull

# Activate virtual environment
source .venv/bin/activate

# Run main.py
python main.py