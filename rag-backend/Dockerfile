# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV RUNNING_IN_DOCKER=true

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if needed (e.g., for psycopg2-binary)
# Some Python libraries require underlying system libraries.
# If you encounter build errors later mentioning missing system libraries,
# uncomment and modify the line below. Common examples include build-essential for C extensions.
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Install pip dependencies
# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Upgrade pip and install requirements
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
# This assumes your FastAPI app code is within an 'app' directory
COPY ./app /app/app

# Copy any other necessary files or directories at the root level (e.g., templates, static)
# COPY ./templates /app/templates

# Expose the port the app runs on (Standard port for Cloud Run)
EXPOSE 8000

# Define the command to run the application using uvicorn
# Use 0.0.0.0 to make it accessible from outside the container
# Cloud Run expects the application to listen on the port specified by the PORT env var OR 8000 by default.
# Using --port 8000 explicitly matches the EXPOSE directive.
# Adjust 'app.main:app' if your FastAPI app instance is defined elsewhere.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 