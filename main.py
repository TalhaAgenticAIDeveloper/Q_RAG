from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import logging
import asyncio
import pandas as pd
from PyPDF2 import PdfReader
from RAG_utils import (
    get_text_chunks,
    get_vector_store,
    user_input_stream,
)

# -----------------------
# Setup Logging
# -----------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# -----------------------
# Initialize FastAPI App
# -----------------------
app = FastAPI(title="RAG Chatbot API")

# -----------------------
# CORS Middleware
# -----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Static Files
# -----------------------
app.mount("/static", StaticFiles(directory="static"), name="static")


# -----------------------
# Helper Functions
# -----------------------

def extract_pdf_text(file_bytes, filename):
    """Extract text from PDF file bytes"""
    try:
        from io import BytesIO
        pdf_file = BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content
        return text
    except Exception as e:
        raise Exception(f"Error reading {filename}: {str(e)}")


def extract_csv_text(file_bytes, filename):
    """Extract text from CSV file bytes"""
    try:
        from io import StringIO
        csv_content = file_bytes.decode('utf-8')
        df = pd.read_csv(StringIO(csv_content))
        return df.to_string(index=False) + "\n"
    except Exception as e:
        raise Exception(f"Error reading {filename}: {str(e)}")


def extract_excel_text(file_bytes, filename):
    """Extract text from Excel file bytes"""
    try:
        from io import BytesIO
        excel_file = BytesIO(file_bytes)
        df = pd.read_excel(excel_file)
        return df.to_string(index=False) + "\n"
    except Exception as e:
        raise Exception(f"Error reading {filename}: {str(e)}")


# -----------------------
# Endpoints
# -----------------------

@app.get("/")
async def root():
    """Serve frontend home page"""
    return FileResponse("static/index.html")


@app.post("/api/upload")
async def upload_files(
    pdf_docs: list[UploadFile] = File(None),
    csv_files: list[UploadFile] = File(None),
    excel_files: list[UploadFile] = File(None),
):
    """Upload and process documents"""
    try:
        raw_text = ""

        # Process PDFs
        if pdf_docs:
            for pdf in pdf_docs:
                content = await pdf.read()
                raw_text += extract_pdf_text(content, pdf.filename)

        # Process CSVs
        if csv_files:
            for csv in csv_files:
                content = await csv.read()
                raw_text += extract_csv_text(content, csv.filename)

        # Process Excel files
        if excel_files:
            for excel in excel_files:
                content = await excel.read()
                raw_text += extract_excel_text(content, excel.filename)

        if not raw_text.strip():
            raise HTTPException(status_code=400, detail="No readable content found!")

        # Process and store
        chunks = get_text_chunks(raw_text)
        get_vector_store(chunks)

        return {
            "status": "success",
            "message": "Files processed and indexed successfully!",
            "chunks_created": len(chunks),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing files: {str(e)}")


@app.post("/api/chat")
async def chat(data: dict):
    """Chat endpoint with streaming response"""
    user_question = data.get("question", "").strip()

    if not user_question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    async def generate_response():
        """Generator for streaming response with delays"""
        try:
            for chunk in user_input_stream(user_question):
                # chunk is already a string from .content
                if chunk:
                    # Split chunk into smaller pieces (words) for better streaming effect
                    words = chunk.split()
                    for word in words:
                        # Add word with space
                        text_piece = word + " "
                        # Add 0.02 second delay between words to make streaming visible
                        await asyncio.sleep(0.02)
                        yield f"data: {json.dumps({'text': text_piece})}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate_response(), media_type="text/event-stream")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "RAG Chatbot API is running"}


# -----------------------
# Run Application
# -----------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
