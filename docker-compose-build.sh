#!/bin/bash

echo "Building and starting all services with Docker Compose..."

# Build and start the containers in detached mode
docker-compose build
docker-compose up -d

echo "All services are now running in the background!"
echo "Flask web interface: http://localhost:5000"
echo "Rasa API: http://localhost:5005"
echo "Actions server: http://localhost:5055"

echo "To see logs, use: docker-compose logs -f"
echo "To stop all services, use: ./docker-compose-cleanup.sh"