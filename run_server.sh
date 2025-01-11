#!/bin/bash

# Load environment variables if .env exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Add src directory to Python path
export PYTHONPATH="${PYTHONPATH}:${PWD}"

# Print startup configuration
echo "Starting OPTIMAT Backend Server..."
echo "--------------------------------"
echo "Host: ${SERVER_HOST}"
echo "Port: ${SERVER_PORT}"
echo "Debug: ${SERVER_DEBUG}"
echo "Workers: ${SERVER_WORKERS}"
echo "--------------------------------"

# Run the server
python src/server.py 