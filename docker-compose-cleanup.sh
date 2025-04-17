#!/bin/bash

echo "Stopping and removing all Docker Compose services..."

# Stop and remove all services defined in docker-compose.yml
docker-compose down

# Optionally remove volumes as well
echo "Do you want to remove Docker volumes as well? (y/n)"
read -r remove_volumes

if [[ "$remove_volumes" == "y" || "$remove_volumes" == "Y" ]]; then
    echo "Removing volumes..."
    docker-compose down -v
    echo "Volumes removed."
fi

echo "All Docker Compose services have been stopped and removed."