#!/bin/bash

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Initialize database
python3 - <<EOF
from database import engine
from models import Base
Base.metadata.create_all(engine)
EOF

echo "Setup complete! Activate the virtual environment with: source venv/bin/activate"
