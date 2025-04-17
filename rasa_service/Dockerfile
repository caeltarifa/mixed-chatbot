FROM python:3.9-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download language model for spaCy
RUN python -m spacy download en_core_web_md

# Copy rasa project
COPY config/ ./config/
COPY data/ ./data/
COPY domain.yml config.yml endpoints.yml credentials.yml ./

# Expose port for Rasa server
EXPOSE 5005

# Entrypoint when container starts
CMD ["rasa", "run", "--cors", "*", "--debug", "--enable-api"]