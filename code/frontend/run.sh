#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Check if a port number argument is provided
if [ $# -eq 0 ]; then
    # Default port number if not provided
    PORT=5000
else
    PORT=$1
fi

# Run the Flask application with the specified port number
python app.py --port $PORT

# Deactivate the virtual environment after running the Flask application
deactivate
