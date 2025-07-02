#!/bin/bash
# TeamCity VCS Script Deployment Script

set -e

echo "=== TeamCity VCS Script Deployment ==="

# Check Python version
python3 --version
if [ $? -ne 0 ]; then
    echo "Error: Python 3 is required"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Verify script can run (dry run check)
echo "Verifying script syntax..."
python3 -m py_compile teamcity-vcs.py

# Check environment variables
if [ -z "$TEAMCITY_ACCESS_TOKEN" ]; then
    echo "Warning: TEAMCITY_ACCESS_TOKEN environment variable not set"
    echo "Set this before running the script in production"
fi

# Make script executable
chmod +x teamcity-vcs.py

echo "=== Deployment Complete ==="
echo "Usage: python3 teamcity-vcs.py > output.csv"
echo "Make sure to set TEAMCITY_ACCESS_TOKEN environment variable"
