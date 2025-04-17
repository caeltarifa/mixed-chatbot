FROM python:3.9-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy action files
COPY actions.py __init__.py ./

# Expose port for Rasa Action server
EXPOSE 5055

# Start Rasa Action server
CMD ["rasa", "run", "actions", "--debug"]