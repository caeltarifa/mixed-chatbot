# Mixed chatbot
Extended chatbot based on Rasa training for physiotherapy and powered by LLM.

## Azure-architectured chatbot
This project uses a four-service microservices architecture:

1. **Rasa Service**: Core NLU and dialogue management
2. **Actions Service**: Custom action handlers for Rasa
3. **Flask UI Service**: Web interface for user interaction
4. **Langchain Service**: Access to the universal data training (next up)

The services communicate with each other via HTTP APIs, using Docker for containerization and Docker Compose for orchestration.

<details>
  <summary><b>Design image</b></summary>
  <img src="https://github.com/user-attachments/assets/f7d45fa5-9f1c-4930-ab6a-f72a9ee79fbb" alt="extended chatbot whether for online and offline service">
</details>

## Running the Application

### Option 1: Using Individual Docker Containers

If you prefer to manage containers individually:

```bash
# Build all Docker containers
./docker-build.sh

# Stop and remove all containers
./docker-cleanup.sh
```

### Option 2: Using Docker Compose (For localhost)

Use the provided scripts for easy Docker Compose management:

```bash
# Build and start all services with Docker Compose
./docker-compose-build.sh

# Stop and remove all Docker Compose services
./docker-compose-cleanup.sh
```

Alternatively, you can run Docker Compose commands directly:

```bash
docker-compose up      # Run in foreground with logs
docker-compose up -d   # Run in background
docker-compose down    # Stop and remove containers
```

Once running, whether individually or Docker Compose, you can access the chat interface at http://localhost:5000.

## Features

- Natural Language Understanding for exercise requests
- Personalized exercise recommendations based on body part and condition
- Interface with real-time chat
- Chat memory for consistent conversations
- Focused recommendations for specific conditions
- Professional physiotherapy guidance
