#!/bin/bash

echo "=========================================="
echo "  AI-Farm - Smart Farming Assistant"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3.8 or higher."
    exit 1
fi

echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Starting AI-Farm application..."
echo ""
echo "Access the application at: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
