#!/bin/bash

# Load environment variables if .env exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Add src directory to Python path
export PYTHONPATH="${PYTHONPATH}:${PWD}"

# Set mock database flag
export USE_MOCK_DB=true

# Print startup configuration
echo "Starting OPTIMAT Mock Backend Server..."
echo "--------------------------------"
echo "Host: 0.0.0.0"
echo "Port: 8000" 
echo "Debug: true"
echo "Workers: 1"
echo "Using Mock Database: true"
echo "--------------------------------"

# Run the server
python src/server.py --debug --mock --workers 1