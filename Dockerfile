# Use an official lightweight Python runtime as a base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# --- CRITICAL ADDITION 1: Install System Dependencies for Playwright ---
# These are Linux libraries required for the Chromium browser engine to run in a minimal image
RUN apt-get update && apt-get install -y \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm1 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
# --------------------------------------------------------------------

# Copy requirements.txt and install Python dependencies (including psycopg2-binary)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- CRITICAL ADDITION 2: Install Browser Binaries ---
# This command downloads the actual Chromium browser executable
RUN playwright install chromium
# ----------------------------------------------------

# Copy the rest of the application source code into the container
COPY . .

# Set the environment variable to make Flask accessible
ENV FLASK_RUN_HOST=0.0.0.0

# The application runs on port 5000 by default (Flask's default)
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"]
