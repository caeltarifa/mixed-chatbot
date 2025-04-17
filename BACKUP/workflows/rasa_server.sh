#!/bin/bash
# Start the Rasa server to handle NLU and dialogue
echo "Starting Rasa server..."
rasa run --enable-api --cors "*" --debug