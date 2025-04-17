#!/bin/bash

echo "Stopping and removing Docker containers..."

# Stop and remove containers if they exist
if [ "$(docker ps -a -q -f name=flask-service)" ]; then
    echo "Stopping and removing Flask service container..."
    docker stop flask-service
    docker rm flask-service
fi

if [ "$(docker ps -a -q -f name=rasa-service)" ]; then
    echo "Stopping and removing Rasa service container..."
    docker stop rasa-service
    docker rm rasa-service
fi

if [ "$(docker ps -a -q -f name=actions-service)" ]; then
    echo "Stopping and removing Actions service container..."
    docker stop actions-service
    docker rm actions-service
fi

echo "All containers stopped and removed."