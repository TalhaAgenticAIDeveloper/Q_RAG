# RAG Chatbot - Docker Setup

## Quick Start with Docker

### Prerequisites
- Docker installed on your system
- `.env` file with `GROQ_API_KEY` configured

### Option 1: Using Docker Compose (Recommended)

1. **Create `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env and add your GROQ_API_KEY
   ```

2. **Build and run:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Frontend: http://localhost:8000
   - API Health: http://localhost:8000/api/health

4. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Option 2: Using Docker Directly

1. **Build the image:**
   ```bash
   docker build -t rag-chatbot:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 \
     --env-file .env \
     -v $(pwd)/faiss_index:/app/faiss_index \
     -v $(pwd)/static:/app/static \
     --name rag-chatbot-api \
     rag-chatbot:latest
   ```

3. **Access the application:**
   - Frontend: http://localhost:8000
   - API Health: http://localhost:8000/api/health

4. **Stop the container:**
   ```bash
   docker stop rag-chatbot-api
   docker rm rag-chatbot-api
   ```

## Features

- **Port 8000**: FastAPI server running with streaming responses
- **Health Check**: Built-in health check endpoint
- **Volume Mounts**: Persistent storage for FAISS index and static files
- **Environment Variables**: Support for `.env` file configuration
- **Automatic Restart**: Container restarts unless stopped manually

## Troubleshooting

### Check logs:
```bash
docker-compose logs -f rag-chatbot
```

### Verify health:
```bash
curl http://localhost:8000/api/health
```

### Rebuild image:
```bash
docker-compose build --no-cache
```
