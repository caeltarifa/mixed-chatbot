#!/bin/bash
# RAG Application - Docker Cleanup Script
# This script removes all Docker resources for the RAG application

set -e  # Exit on any error

# Configuration (must match docker-build.sh)
IMAGE_NAME="rag-app"
CONTAINER_NAME="rag-app"

echo "🧹 Starting RAG Application Cleanup..."
echo "======================================="

# Stop container if running
echo "⏹️  Stopping container: $CONTAINER_NAME"
if docker stop $CONTAINER_NAME 2>/dev/null; then
    echo "   ✅ Container stopped successfully"
else
    echo "   ℹ️  Container was not running"
fi

# Remove container
echo "🗑️  Removing container: $CONTAINER_NAME"
if docker rm $CONTAINER_NAME 2>/dev/null; then
    echo "   ✅ Container removed successfully"
else
    echo "   ℹ️  Container was already removed"
fi

# Remove image
echo "🗑️  Removing image: $IMAGE_NAME"
if docker rmi $IMAGE_NAME 2>/dev/null; then
    echo "   ✅ Image removed successfully"
else
    echo "   ℹ️  Image was already removed or doesn't exist"
fi

# Clean up dangling images and unused resources
echo "🧽 Cleaning up unused Docker resources..."
docker system prune -f

echo ""
echo "✅ Cleanup completed successfully!"
echo "======================================="
echo "📂 Your data is preserved in:"
echo "   - rag_app/data_ingestion/raw_pdfs/"
echo "   - rag_app/document_store/"
echo ""
echo "🚀 To rebuild and run: ./docker-build.sh"