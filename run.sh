#!/bin/bash

# OmniStream Archiver Startup Script
# This script activates the virtual environment and launches the application

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
    playwright install chromium
else
    source venv/bin/activate
fi

# Launch the application
echo "Starting OmniStream Archiver..."
python main.py
