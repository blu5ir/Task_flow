# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy just the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code into the container
COPY . .

# Expose the port your Flask app is running on (from your earlier code, this is 5001)
EXPOSE 5001

# Define the command to run your app
# (If your main file is named something else like taskflow.py, change it here)
CMD ["python", "app.py"]
