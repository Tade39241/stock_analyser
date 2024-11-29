#!/bin/bash

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install required packages
pip install -r requirements.txt

# Check if a port number argument is provided
if [ $# -eq 0 ]; then
    # Default port number if not provided
    PORT=5000
else
    PORT=$1
fi

echo "Setup completed. Virtual environment created and dependencies installed."
echo "Run the application with 'bash run.sh $PORT' or './run.sh $PORT'."
