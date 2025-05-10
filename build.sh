#!/usr/bin/env bash
# Exit on error
set -e

echo "Setting up Python environment..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Making sure the database directory exists..."
mkdir -p instance

echo "Initializing the database..."
python init_db.py

echo "Setup complete! The application is ready to be started."

# Start the application (uncomment the actual start command for your app)
# python app.py 