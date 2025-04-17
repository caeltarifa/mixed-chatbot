#!/bin/bash

echo "Building Docker containers..."

# Build the Flask service container
echo "Building Flask service container..."
docker build -t physiotherapy-bot-flask:latest ./flask_service

# Build the Rasa service container
echo "Building Rasa service container..."
docker build -t physiotherapy-bot-rasa:latest ./rasa_service

# Build the Actions service container
echo "Building Actions service container..."
docker build -t physiotherapy-bot-actions:latest ./actions_service

echo "All containers built successfully!"

echo "Flask app is running on http://localhost:5000"
docker run -d -p 5000:5000 --name flask-service physiotherapy-bot-flask

echo "Rasa API is running on http://localhost:5005"
docker run -d -p 5005:5005 --name rasa-service physiotherapy-bot-rasa

echo "Actions server is running on http://localhost:5055"
docker run -d --name actions-service physiotherapy-bot-actions