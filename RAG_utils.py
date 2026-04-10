# rag_utils.py

import os
import logging
import pandas as pd
from PyPDF2 import PdfReader
from dotenv import load_dotenv

# LangChain Imports
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Embeddings (Offline)
from langchain_community.embeddings import HuggingFaceEmbeddings

# LLM (Groq - same as your requirement)
from langchain_groq import ChatGroq

# ✅ NEW: Langfuse Integration
from langfuse.langchain import CallbackHandler

# -----------------------
# Setup Logging (Pure Python - works everywhere)
# -----------------------
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger.setLevel(logging.DEBUG)

# -----------------------
# Load Environment Variables
# -----------------------
load_dotenv()

# ✅ NEW: Initialize Langfuse CallbackHandler (Global)
langfuse_handler = CallbackHandler()

# -----------------------
# LLM Initialization
# -----------------------
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)

# -----------------------
# File Text Extraction
# -----------------------

def get_pdf_text(pdf_docs):
    """Extract text from PDF files"""
    text = ""
    for pdf in pdf_docs:
        try:
            reader = PdfReader(pdf)
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content
        except Exception as e:
            logger.error(f"Error reading {pdf.name}: {e}")
    return text


def get_csv_text(csv_files):
    """Extract text from CSV files"""
    text = ""
    for csv in csv_files:
        try:
            df = pd.read_csv(csv)
            text += df.to_string(index=False) + "\n"
        except Exception as e:
            logger.error(f"Error reading {csv.name}: {e}")
    return text


def get_excel_text(excel_files):
    """Extract text from Excel files"""
    text = ""
    for excel in excel_files:
        try:
            df = pd.read_excel(excel)
            text += df.to_string(index=False) + "\n"
        except Exception as e:
            logger.error(f"Error reading {excel.name}: {e}")
    return text


# -----------------------
# Text Chunking
# -----------------------

def get_text_chunks(text):
    """Split text into chunks for embeddings"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    return splitter.split_text(text)


# -----------------------
# Vector Store (FAISS + Offline Embeddings)
# -----------------------

def get_vector_store(text_chunks):
    """
    Create FAISS vector store using HuggingFace embeddings (offline)
    """
    
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)

    vector_store.save_local("faiss_index")

    return vector_store


# -----------------------
# Conversational Chain
# -----------------------

def get_conversational_chain():
    """Create QA chain with strict context usage"""

    prompt_template = """
    You are a careful analyst who must answer using ONLY the provided context.

    Rules:
    1) Do NOT guess.
    2) Use ONLY given context.
    3) For numeric questions:
       - Show calculations as 'Calc:'
       - If incomplete: say "Partial result (based on visible context)"
    4) If answer not found:
       "answer is not available in the provided context."

    Context:
    {context}

    Question:
    {question}

    Answer:
    """

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    def format_docs(docs):
        return "\n".join([doc.page_content for doc in docs])

    chain = (
        {
            "context": lambda x: format_docs(x["input_documents"]),
            "question": lambda x: x["question"]
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain


# -----------------------
# User Query Handling
# -----------------------

def user_input(user_question):
    """
    Handle user query (non-streaming):
    - Load FAISS
    - Perform similarity search
    - Pass to LLM with Langfuse tracing
    """

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vector_store = FAISS.load_local(
        "faiss_index",
        embeddings,
        allow_dangerous_deserialization=True
    )

    docs = vector_store.similarity_search(user_question)

    chain = get_conversational_chain()

    # ✅ NEW: Pass Langfuse callback with metadata
    response = chain.invoke(
        {
            "input_documents": docs,
            "question": user_question
        },
        config={
            "callbacks": [langfuse_handler],
            "metadata": {
                "user_question": user_question,
                "retrieved_docs_count": len(docs),
                "trace_type": "non_streaming"
            }
        }
    )

    return response


def user_input_stream(user_question):
    """
    Handle user query with streaming response (Langfuse compatible):
    - Load FAISS
    - Perform similarity search
    - Stream LLM response via chain.stream() with Langfuse tracing
    """

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vector_store = FAISS.load_local(
        "faiss_index",
        embeddings,
        allow_dangerous_deserialization=True
    )

    docs = vector_store.similarity_search(user_question)

    # Format docs
    def format_docs(docs):
        return "\n".join([doc.page_content for doc in docs])

    context = format_docs(docs)

    # Create streaming prompt
    prompt_template = """
    You are a careful analyst who must answer using ONLY the provided context.

    Rules:
    1) Do NOT guess.
    2) Use ONLY given context.
    3) For numeric questions:
       - Show calculations as 'Calc:'
       - If incomplete: say "Partial result (based on visible context)"
    4) If answer not found:
       "answer is not available in the provided context."

    Context:
    {context}

    Question:
    {question}

    Answer:
    """

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    # Create streaming chain (no StrOutputParser for true token streaming)
    chain = prompt | llm

    # ✅ NEW: Pass Langfuse callback with metadata to chain.stream()
    for chunk in chain.stream(
        {
            "context": context,
            "question": user_question
        },
        config={
            "callbacks": [langfuse_handler],
            "metadata": {
                "user_question": user_question,
                "retrieved_docs_count": len(docs),
                "trace_type": "streaming"
            }
        }
    ):
        # chunk is an AIMessage with content attribute
        yield chunk.content

