#!/bin/bash
echo "--- Pipeline Stage: Deployment ---"
echo "Creating Production Directory..."
mkdir -p dist/
echo "Copying files to production..."
cp app.py requirements.txt dist/
echo "Deployment successful! App 'deployed' to ./dist folder."
