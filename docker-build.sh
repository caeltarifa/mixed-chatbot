#!/bin/bash
# RAG Application - Docker Build Script
# This script builds and runs the RAG application with proper volume mounting

set -e  # Exit on any error

# Configuration
IMAGE_NAME="rag-app"
CONTAINER_NAME="rag-app"
HOST_PORT="5000"

echo "🚀 Starting RAG Application Docker Build..."
echo "================================================"

# Check if Gemini API key is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  Warning: GEMINI_API_KEY not set!"
    echo "   Please set it with: export GEMINI_API_KEY='your-api-key'"
    echo "   The app will use a default key for now."
fi

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p rag_app/data_ingestion/raw_pdfs
mkdir -p rag_app/document_store

# Build Docker image
echo "🔨 Building Docker image: $IMAGE_NAME..."
docker build -t $IMAGE_NAME .

# Stop and remove existing container if it exists
echo "🧹 Cleaning up existing container..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Run new container with volume mounts and environment variables
echo "🚀 Running RAG Application container..."
docker run -d \
  --name $CONTAINER_NAME \
  -p $HOST_PORT:8000 \
  -e GEMINI_API_KEY="${GEMINI_API_KEY:-default_gemini_key}" \
  -e LOG_LEVEL="INFO" \
  -v $(pwd)/rag_app/data_ingestion/raw_pdfs:/app/rag_app/data_ingestion/raw_pdfs \
  -v $(pwd)/rag_app/document_store:/app/rag_app/document_store \
  $IMAGE_NAME

echo "✅ RAG Application is now running!"
echo "================================================"
echo "🌐 Access at: http://localhost:$HOST_PORT"
echo "📋 Container name: $CONTAINER_NAME"
echo ""
echo "📝 Useful commands:"
echo "   View logs:     docker logs $CONTAINER_NAME"
echo "   Stop app:      docker stop $CONTAINER_NAME"
echo "   Interactive:   docker exec -it $CONTAINER_NAME python main.py --interactive"
echo "   Status check:  docker exec -it $CONTAINER_NAME python main.py --status"
echo ""
echo "📂 Add PDF files to: rag_app/data_ingestion/raw_pdfs/"
echo "🧹 Clean up with: ./docker-cleanup.sh"