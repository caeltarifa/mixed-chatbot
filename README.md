# RAG Application with Haystack and Gemini

A local Retrieval Augmented Generation (RAG) application built with Haystack framework and Google Gemini API integration. The application processes PDF documents, creates vector embeddings, and enables intelligent querying using natural language.

## Features

- **PDF Document Processing**: Automatically ingests and processes PDF documents
- **Vector Search**: Uses sentence transformers for semantic document retrieval
- **Gemini AI Integration**: Leverages Google's Gemini API for response generation
- **Persistent Storage**: SQLite database for document and vector storage
- **Docker Support**: Containerized deployment for easy setup
- **Interactive CLI**: Command-line interface for querying and management
- **Modular Architecture**: Clean separation of concerns with dedicated services

## Quick Start

### Prerequisites

- Python 3.9+
- Docker (optional)
- Google Gemini API key

### Installation (Docker Only - Using Bash Scripts)

**Important**: This application is designed to run with Docker using the provided bash scripts. The Dockerfile, docker-build.sh, and docker-cleanup.sh work together as an integrated system.

#### Quick Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd rag-application
   ```

2. **Set your Gemini API key:**
   ```bash
   export GEMINI_API_KEY="your-actual-api-key-here"
   ```

3. **Make scripts executable and run:**
   ```bash
   chmod +x docker-build.sh docker-cleanup.sh
   ./docker-build.sh
   ```

That's it! The build script will automatically:
- Create necessary directories
- Build the Docker image
- Stop any existing containers
- Run the new container with proper volume mounts
- Display helpful usage commands

#### Alternative: Local Python Installation (Not Recommended)

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd rag-application
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your Gemini API key:**
   ```bash
   export GEMINI_API_KEY="your-actual-api-key-here"
   ```

4. **Run the application:**
   ```bash
   python main.py --interactive
   ```

## Usage

### Command Line Options

- `--status`: Show system status and health check
- `--health`: Perform detailed health check
- `--clear-index`: Clear all indexed documents
- `--index`: Index all PDF documents in the data directory
- `--force-reindex`: Force reindexing of all documents
- `--summary`: Generate summary of all indexed documents
- `--query "your question"`: Ask a specific question
- `--interactive`: Start interactive query mode
- `--help`: Show help information

### Adding PDF Documents

1. Place your PDF files in the `rag_app/data_ingestion/raw_pdfs/` directory
2. Run indexing: `python main.py --index`
3. Start querying: `python main.py --interactive`

### Interactive Mode

Start interactive mode to have conversations with your documents:

```bash
python main.py --interactive
```

Then ask questions like:
- "What is the main topic of the documents?"
- "Summarize the key findings"
- "What recommendations are mentioned?"

## Docker Management

### Build and Run Commands

```bash
# Build the image
docker build -t rag-app .

# Run with environment variables
docker run -it \
  -e GEMINI_API_KEY="your-api-key" \
  -e LOG_LEVEL="INFO" \
  -e CHUNK_SIZE="1000" \
  -e TOP_K="5" \
  -v $(pwd)/rag_app/data_ingestion/raw_pdfs:/app/rag_app/data_ingestion/raw_pdfs \
  -v $(pwd)/rag_app/document_store:/app/rag_app/document_store \
  rag-app

# Clean up containers and images
chmod +x docker-cleanup.sh
./docker-cleanup.sh
```

### Persistent Data

The Docker setup includes volume mounts to persist:
- **PDF documents**: `rag_app/data_ingestion/raw_pdfs/`
- **Database**: `rag_app/document_store/`

### Bash Scripts

The project includes convenient bash scripts for Docker management:

#### docker-build.sh
Builds and runs the Docker container automatically:

```bash
chmod +x docker-build.sh
./docker-build.sh
```

This script will:
- Build the Docker image as `haystack-rag-app:latest`
- Run the container on port 5000
- Provide helpful commands for logs and interaction

#### docker-cleanup.sh
Cleans up Docker resources:

```bash
chmod +x docker-cleanup.sh
./docker-cleanup.sh
```

This script will:
- Stop and remove the `rag-app` container
- Remove the `rag-application` image
- Clean up dangling Docker images

**Note:** Make sure to set your `GEMINI_API_KEY` environment variable before running the build script for the application to work properly.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key (required) | `default_gemini_key` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CHUNK_SIZE` | Document chunk size | `1000` |
| `CHUNK_OVERLAP` | Chunk overlap size | `200` |
| `TOP_K` | Number of relevant documents to retrieve | `5` |
| `MAX_TOKENS` | Maximum tokens for generation | `2048` |
| `TEMPERATURE` | Generation temperature | `0.3` |

## Project Structure

```
rag-application/
├── main.py                          # Main application entry point
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Docker configuration
├── docker-build.sh                  # Docker build script
├── docker-cleanup.sh               # Docker cleanup script
├── README.md                        # This file
└── rag_app/
    ├── config/                      # Configuration settings
    ├── data_ingestion/              # PDF loading and preprocessing
    │   └── raw_pdfs/               # Place your PDF files here
    ├── document_store/              # SQLite database and vector storage
    ├── models/                      # Embedding and generative services
    ├── pipelines/                   # Indexing and query pipelines
    ├── services/                    # Main RAG service
    └── utils/                       # Utility functions
```

## Architecture

