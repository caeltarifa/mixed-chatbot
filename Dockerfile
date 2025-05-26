# RAG Application Dockerfile
# Optimized for easy deployment with bash scripts

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PDF processing
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p rag_app/data_ingestion/raw_pdfs \
    && mkdir -p rag_app/document_store \
    && chmod -R 755 rag_app

# Set environment variables for the application
ENV PYTHONPATH=/app
ENV GEMINI_API_KEY=default_gemini_key
ENV LOG_LEVEL=INFO
ENV CHUNK_SIZE=1000
ENV CHUNK_OVERLAP=200
ENV TOP_K=5
ENV MAX_TOKENS=2048
ENV TEMPERATURE=0.3

# Expose port for potential web interface
EXPOSE 8000

# Create non-root user for security
RUN useradd -m -u 1000 raguser \
    && chown -R raguser:raguser /app
USER raguser

# Health check to ensure application is working
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python main.py --status || exit 1

# Default command - interactive mode for CLI usage
CMD ["python", "main.py", "--interactive"]
