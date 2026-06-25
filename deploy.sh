#!/bin/bash
echo "Starting CI/CD Pipeline..."

# 1. Simulate Testing
echo "Running tests..."
# python -m pytest tests/
echo "Tests passed!"

# 2. Simulate Building
echo "Building application..."
# docker build -t my-app .
echo "Build complete."

# 3. Simulate Deployment
echo "Deploying to local production environment..."
# cp -r . /var/www/my-app
echo "Deployment successful! Your app is live at http://localhost:5000"
