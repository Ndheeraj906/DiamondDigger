FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy dependencies
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port (Cloud Run sets the PORT environment variable)
EXPOSE 8080

# Command to run the application with Gunicorn
# Using --timeout 300 to allow the AI up to 5 minutes to generate the response
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 300 app:app
