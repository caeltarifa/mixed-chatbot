FROM python:3.9-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py ./
COPY static/ ./static/
COPY templates/ ./templates/

# Expose port for Flask app
EXPOSE 5000

# Start Flask app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "--reload", "app:app"]