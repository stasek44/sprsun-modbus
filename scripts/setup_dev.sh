#!/bin/bash
# Development environment setup

echo "Setting up development environment for SPRSUN Modbus integration..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install development dependencies
echo "Installing dependencies..."
pip install -r requirements_dev.txt

# Install pre-commit hooks (if using)
if [ -f ".pre-commit-config.yaml" ]; then
    pre-commit install
fi

echo "✅ Development environment ready!"
echo "To activate: source .venv/bin/activate"
