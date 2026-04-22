#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
LOGS_DIR="$SCRIPT_DIR/logs"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate" || source "$VENV_DIR/Scripts/activate"

pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt"

mkdir -p "$LOGS_DIR"

TIMESTAMP=$(date +"%Y-%m-%d_%H%_M%_S")
RUN_LOGS_DIR="$LOGS_DIR/$TIMESTAMP"
mkdir -p "$RUN_LOGS_DIR"
export TEST_LOGS_DIR="$RUN_LOGS_DIR"

if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running."
    deactivate
    exit 1
fi

set +e
pytest $(ls ${SCRIPT_DIR}/test_*.py)
result=$?

if [ $result -eq 0 ]; then
    echo "Tests passed!"
else
    echo "Tests failed!"
    echo "Logs: $RUN_LOGS_DIR"
fi

deactivate
exit $result
