# Quanticept RAG Chatbot

A retrieval-augmented generation (RAG) chatbot that allows you to upload PDFs and ask questions about their content.

## Features

- **PDF Upload & Processing**: Upload PDF documents to build a searchable knowledge base
- **Vector Search**: Uses FAISS for efficient semantic search across documents
- **AI-Powered Responses**: Leverages Groq LLM with HuggingFace embeddings for intelligent question answering
- **Web Interface**: Simple, intuitive UI for uploading documents and chatting
- **Monitoring**: Integrated with Langfuse for tracking and analytics

## Tech Stack

- **Backend**: FastAPI with uvicorn
- **LLM Framework**: LangChain with Groq API
- **Embeddings**: HuggingFace sentence-transformers (offline)
- **Vector DB**: FAISS
- **Document Processing**: PyPDF2
- **Monitoring**: Langfuse

## Setup

### Prerequisites

- Python 3.8+
- GROQ_API_KEY (set in `.env`)

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API key:
   ```
   GROQ_API_KEY=your_key_here
   ```

## Usage

Start the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

- **Web UI**: Visit `http://localhost:8000/static/index.html`
- **API Docs**: Visit `http://localhost:8000/docs`

### Upload Documents

Use the web interface to upload PDF files. They will be processed and indexed automatically.

### Query

Ask questions about your uploaded documents through the chat interface or API endpoints.

## Project Structure

```
.
├── main.py              # FastAPI application entry point
├── RAG_utils.py         # RAG utilities (embeddings, LLM, vector store)
├── requirements.txt     # Python dependencies
├── static/              # Web UI files
│   ├── index.html
│   ├── script.js
│   └── styles.css
└── faiss_index/         # Persisted FAISS vector index
    └── index.faiss
```

## Environment Variables

- `GROQ_API_KEY`: Your Groq API key for LLM access

## Notes

- Embeddings are generated offline using HuggingFace models
- The FAISS index persists locally for future sessions
- CORS is enabled for broad client access
