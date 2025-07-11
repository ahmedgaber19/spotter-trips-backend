#!/bin/bash

# Build script for Vercel deployment
echo "Starting build process..."

# Install dependencies
echo "Installing Python dependencies..."
python3.9 -m pip install -r requirements.txt

# Create static files directory
echo "Creating static files directory..."
mkdir -p staticfiles_build

# Collect static files
echo "Collecting static files..."
python3.9 manage.py collectstatic --noinput --clear

echo "Build completed successfully!"
