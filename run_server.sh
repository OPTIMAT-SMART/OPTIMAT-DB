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

# Run the server
python src/server.py --debug --mock  