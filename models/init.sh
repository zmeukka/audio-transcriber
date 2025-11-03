#!/bin/bash
# Wrapper script for Unix/Linux systems
# Finds Python and runs the initialization script with virtual environment support

cd "$(dirname "$0")"

# Check if virtual environment exists and is activated
venv_path="../.venv"
is_venv_activated=false

if [ -n "$VIRTUAL_ENV" ]; then
    is_venv_activated=true
fi

if [ -d "$venv_path" ]; then
    if [ "$is_venv_activated" = false ]; then
        echo "Virtual environment found but not activated"
        echo "Activating virtual environment..."
        source "$venv_path/bin/activate"
        if [ $? -eq 0 ]; then
            python_exe="$venv_path/bin/python"
        else
            echo "Failed to activate virtual environment, falling back to system Python"
            python_exe=""
        fi
    else
        echo "Virtual environment is active"
        python_exe="$venv_path/bin/python"
    fi
else
    echo "No virtual environment found at $venv_path"
    echo "Run ./setup_venv.sh from project root to create one"
    python_exe=""
fi

# If no venv python, try to find system Python
if [ -z "$python_exe" ]; then
    for exe in python3 python py; do
        if command -v "$exe" >/dev/null 2>&1; then
            python_exe="$exe"
            break
        fi
    done
fi

if [ -n "$python_exe" ]; then
    echo "Using Python: $python_exe"
    exec "$python_exe" init_models.py "$@"
else
    echo "Python not found. Please install Python 3.6+ and add it to PATH"
    echo "Or run ./setup_venv.sh from project root to create virtual environment"
    exit 1
fi

