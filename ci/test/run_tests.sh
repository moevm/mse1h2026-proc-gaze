#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
LOGS_DIR="$SCRIPT_DIR/logs"

if [ ! -d "$VENV_DIR" ]; then
    echo "Setting up virtual environment for testing..."
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created at $VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
echo "Installing dependencies..."
pip install --upgrade pip
pip install pytest requests sqlalchemy asyncpg pydantic
echo "Dependencies installed successfully!"

if [ ! -d "$LOGS_DIR" ]; then
    echo "Creating logs directory at $LOGS_DIR"
    mkdir -p "$LOGS_DIR"
    echo "Logs directory created successfully!"
else
    echo "Logs directory already exists at $LOGS_DIR"
fi

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RUN_LOGS_DIR="$LOGS_DIR/run_$TIMESTAMP"
mkdir -p "$RUN_LOGS_DIR"
echo "Test run logs will be stored in: $RUN_LOGS_DIR"

export TEST_LOGS_DIR="$RUN_LOGS_DIR"

if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running."
    exit 1
fi

set +e
pytest "$SCRIPT_DIR/test_backend_student.py" \
    -vvv -s \
    --log-cli-level=INFO \
    --log-cli-format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'

result=$?

[[ ${result} = 0 ]] && echo "Tests passed!" || echo "Tests failed!"

deactivate
exit ${result}