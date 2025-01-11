#!/bin/bash

# Load environment variables if .env exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Add src directory to Python path
export PYTHONPATH="${PYTHONPATH}:${PWD}"

# Print test configuration
echo "Running OPTIMAT Backend Tests..."
echo "--------------------------------"

# Run the tests with strict asyncio mode and exit on first failure
python tests/create_mock_db.py