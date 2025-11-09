# Use an official lightweight Python runtime as a base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements.txt and install Python dependencies
# The requirements are: requests, Flask, nba_api, pytz
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium

# Copy the rest of the application source code into the container
# This includes app.py, the api/, templates/, static/, and utils/ directories.
COPY . .

# Set the environment variable to make Flask accessible from outside the container's localhost
# You could also modify the app.py to explicitly call app.run(host='0.0.0.0')
ENV FLASK_RUN_HOST=0.0.0.0

# The application runs on port 5000 by default (Flask's default)
EXPOSE 5000

# Command to run the application using the entry point defined in app.py
CMD ["python", "app.py"]
