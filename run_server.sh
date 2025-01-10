#!/bin/bash

# Load environment variables if .env exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Add src directory to Python path
export PYTHONPATH="${PYTHONPATH}:${PWD}"

# Default values
HOST=${SERVER_HOST:-0.0.0.0}
PORT=${SERVER_PORT:-8000}
WORKERS=${WORKERS:-1}

# Help function
show_help() {
    echo "Usage: ./run_server.sh [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -d, --debug    Run in debug mode"
    echo "  -p PORT        Specify port number (default: 8000)"
    echo "  -w WORKERS     Specify number of workers (default: 1)"
    echo
    echo "Example:"
    echo "  ./run_server.sh -d -p 5000 -w 4"
}

# Parse command line arguments
DEBUG_MODE=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--debug)
            DEBUG_MODE="--debug"
            shift
            ;;
        -p)
            PORT="$2"
            shift 2
            ;;
        -w)
            WORKERS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Print startup configuration
echo "Starting OPTIMAT Backend Server..."
echo "--------------------------------"
echo "Host: $HOST"
echo "Port: $PORT"
echo "Debug: ${DEBUG_MODE:-false}"
echo "Workers: $WORKERS"
echo "--------------------------------"

# Run the server
python src/server.py --host "$HOST" --port "$PORT" --workers "$WORKERS" $DEBUG_MODE 