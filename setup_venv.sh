#!/bin/bash
# Setup Virtual Environment for Audio Transcriber
# Creates .venv and installs required packages

FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force|-f)
            FORCE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--force|-f]"
            exit 1
            ;;
    esac
done

cd "$(dirname "$0")"

# Check if .venv exists
if [ -d ".venv" ]; then
    if [ "$FORCE" = true ]; then
        echo "Removing existing .venv..."
        rm -rf .venv
    else
        echo ".venv already exists. Use --force to recreate"
        echo "To activate: source .venv/bin/activate"
        exit 0
    fi
fi

# Find Python executable
for python_exe in python3 python py; do
    if command -v "$python_exe" >/dev/null 2>&1; then
        version=$($python_exe --version 2>&1)
        echo "Found Python: $version"
        foundPython="$python_exe"
        break
    fi
done

if [ -z "$foundPython" ]; then
    echo "Python not found. Please install Python 3.6+ and add it to PATH"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
"$foundPython" -m venv .venv

if [ $? -ne 0 ]; then
    echo "Failed to create virtual environment"
    exit 1
fi

echo "Virtual environment created successfully!"

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install requirements if they exist
if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt

    if [ $? -eq 0 ]; then
        echo "Requirements installed successfully!"
    else
        echo "Failed to install some requirements"
    fi
else
    echo "No requirements.txt found, skipping package installation"
fi

echo ""
echo "Setup completed!"
echo "To activate the environment: source .venv/bin/activate"
echo "To deactivate: deactivate"
echo ""
echo "Now you can run: cd models && ./init.sh"
