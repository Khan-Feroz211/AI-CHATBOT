#!/bin/bash
# setup.sh - Install all dependencies

echo "Setting up AI Chatbot ML Project..."

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
source venv/Scripts/activate 2>/dev/null || .\venv\Scripts\activate

# Install base requirements
pip install -r requirements/base.txt

# Install local ML requirements
pip install -r requirements/ml-local.txt

# Install API requirements
pip install -r requirements/api.txt

echo "Setup complete!"
echo "To activate virtual environment:"
echo "  Windows: .\venv\Scripts\activate"
echo "  Linux/Mac: source venv/bin/activate"
