"""
FastAPI backend for the AI Study Assistant.

Main responsibilities:
- Accept PDF uploads and extract / chunk text.
- Store and search chunks in a local ChromaDB collection.
- Call Ollama to answer questions using the most relevant chunks as context.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

import io

import chromadb
from chromadb.utils import embedding_functions
import PyPDF2
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Base URL for the local Ollama HTTP API.
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"

# Default and fallback models to try in order.
DEFAULT_MODEL = "llama3.2:1b"
FALLBACK_MODELS: List[str] = ["llama3.2:1b", "llama3.2", "llama3:1b", "tinyllama", "phi"]

# Name of the Chroma collection where we store document chunks.
COLLECTION_NAME = "study_docs"


# ---------------------------------------------------------------------------
# Application & database setup
# ---------------------------------------------------------------------------

# Create FastAPI app
app = FastAPI(title="AI Study Assistant API")

# Allow frontend to talk to backend (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ChromaDB client and embedding function once at startup
chroma_client = chromadb.Client()
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)


def get_or_create_collection() -> chromadb.Collection:
    """
    Get the ChromaDB collection used to store study documents,
    creating it if it does not already exist.
    """
    try:
        return chroma_client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=sentence_transformer_ef,
        )
    except Exception:
        # Collection does not exist yet – create a new one.
        return chroma_client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=sentence_transformer_ef,
        )


# Global collection handle reused by the endpoints.
collection = get_or_create_collection()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Question(BaseModel):
    """Request body for the /ask endpoint."""

    question: str


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract plain text from a PDF byte stream.

    This uses PyPDF2 to iterate through all pages and concatenate their text.
    """
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    text_chunks: List[str] = []

    for page in pdf_reader.pages:
        # Some PDFs may return None for pages without text, so guard against it.
        page_text = page.extract_text() or ""
        text_chunks.append(page_text)

    return "".join(text_chunks)


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split long text into overlapping chunks for better semantic search.

    - chunk_size: maximum characters per chunk.
    - overlap:    number of characters that overlap between consecutive chunks.
    """
    if not text:
        return []

    chunks: List[str] = []
    start = 0

    # Slide a window over the text with the given overlap.
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += max(chunk_size - overlap, 1)

    return chunks


def get_available_models() -> List[str]:
    """
    Ask Ollama for the list of available models.

    Returns a list of model names, or an empty list on failure.
    """
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=5)
        if response.status_code != 200:
            return []

        models = response.json().get("models", [])
        return [m.get("name", "") for m in models]
    except Exception:
        # On any network / parsing error just fall back to an empty list.
        return []


def query_ollama(
    prompt: str,
    model: str = DEFAULT_MODEL,
    fallback_models: Optional[Iterable[str]] = None,
) -> str:
    """
    Call the Ollama /generate endpoint with automatic model fallbacks.

    Tries the requested `model` first, then any models in `fallback_models`.
    On network errors, timeouts, or unexpected response formats it either
    tries the next model or raises a descriptive Exception.
    """
    if fallback_models is None:
        fallback_models = FALLBACK_MODELS

    # Build a deduplicated list: primary model first, then fallbacks.
    models_to_try = [model] + [m for m in fallback_models if m != model]
    last_error: Optional[str] = None

    for attempt_model in models_to_try:
        try:
            response = requests.post(
                OLLAMA_GENERATE_URL,
                json={
                    "model": attempt_model,
                    "prompt": prompt,
                    "stream": False,  # We want a simple JSON response, not a stream.
                },
                timeout=90,  # Increased timeout for slower models.
            )

            if response.status_code == 200:
                data: Dict[str, Any] = response.json()
                if "response" in data:
                    return str(data["response"])

                raise Exception(f"Unexpected Ollama response format: {data}")

            # Non-200: inspect body for more info.
            error_msg = f"Ollama returned status {response.status_code}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_msg += f": {error_data['error']}"
                    last_error = str(error_data["error"])
            except Exception:
                error_msg += f": {response.text[:200]}"
                last_error = error_msg

            # For memory/buffer errors, automatically try next model.
            if "unable to allocate" in error_msg.lower() or "buffer" in error_msg.lower():
                continue

            raise Exception(error_msg)

        except requests.exceptions.ConnectionError:
            # If Ollama is not reachable at all, no point in trying other models.
            raise Exception("Cannot connect to Ollama. Is Ollama running? Start it with: ollama serve")
        except requests.exceptions.Timeout:
            # On timeout, try the next model if available; otherwise raise.
            if attempt_model != models_to_try[-1]:
                continue
            raise Exception("Ollama request timed out. The model might be too slow or not responding.")
        except Exception as exc:
            # On any other error – if this was the last model, raise; otherwise keep trying.
            if attempt_model == models_to_try[-1]:
                raise Exception(f"Ollama error: {exc}")
            last_error = str(exc)
            continue

    # If we get here, all models failed.
    available = get_available_models()
    error_suggestion = f"All models failed. Last error: {last_error}\n\n"
    error_suggestion += "Try:\n"
    error_suggestion += "1. Restart Ollama: Close and run 'ollama serve' again\n"
    error_suggestion += "2. Free up RAM: Close other applications\n"
    if available:
        error_suggestion += f"3. Available models: {', '.join(available[:5])}\n"
    else:
        error_suggestion += "3. Install a smaller model: 'ollama pull tinyllama'\n"

    raise Exception(error_suggestion)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def read_root() -> Dict[str, str]:
    """Simple health check to confirm that the API is running."""

    return {"message": "AI Study Assistant API is running with Ollama"}


@app.get("/health")
def health_check() -> Dict[str, Any]:
    """
    Check whether Ollama is reachable and list some model metadata.

    This endpoint is what the frontend uses to show system status and give
    quick hints about which models are installed.
    """
    try:
        # Try to list models to check if Ollama is running.
        response = requests.get(OLLAMA_TAGS_URL, timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]

            return {
                "status": "healthy",
                "ollama": "running",
                "models": model_names,
                "default_model": DEFAULT_MODEL,
                "model_available": any(DEFAULT_MODEL in name for name in model_names),
                "recommended_small_models": [
                    m for m in model_names if any(x in m.lower() for x in ["tiny", "1b", "phi"])
                ],
            }

        # Ollama responded but not with a success status code.
        return {
            "status": "unhealthy",
            "ollama": "responding but error",
            "error": f"Status {response.status_code}",
        }

    except requests.exceptions.ConnectionError:
        return {
            "status": "unhealthy",
            "ollama": "not running",
            "error": "Cannot connect to Ollama. Please run 'ollama serve' in terminal.",
        }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "ollama": "error",
            "error": str(exc),
        }


@app.get("/models")
def list_models() -> Dict[str, Any]:
    """
    Return a list of models that Ollama knows about.

    Helpful for debugging and for letting users choose which model to use.
    """
    try:
        response = requests.get(OLLAMA_TAGS_URL, timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_info = [
                {
                    "name": m.get("name", ""),
                    "size": m.get("size", 0),
                    "modified": m.get("modified_at", ""),
                }
                for m in models
            ]
            return {
                "status": "success",
                "models": model_info,
                "count": len(model_info),
            }

        return {
            "status": "error",
            "error": f"Ollama returned status {response.status_code}",
        }

    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "error": "Cannot connect to Ollama. Please run 'ollama serve' in terminal.",
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
        }


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Ingest a PDF and index it in the vector database.

    Steps:
    1. Read the uploaded PDF into memory.
    2. Extract its text content.
    3. Split the text into overlapping chunks.
    4. Store chunks, ids, and metadata in ChromaDB.
    """
    try:
        # Read uploaded file into memory.
        content = await file.read()

        # Extract plain text from the PDF bytes.
        text = extract_text_from_pdf(content)

        if not text.strip():
            raise HTTPException(status_code=400, detail="No text found in PDF")

        # Break text into smaller chunks for semantic search.
        chunks = chunk_text(text)

        if not chunks:
            raise HTTPException(status_code=400, detail="Failed to generate chunks from PDF text")

        # Build stable ids and simple metadata for each chunk.
        ids = [f"{file.filename}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": file.filename, "chunk": i} for i in range(len(chunks))]

        # Insert all chunks into the vector store.
        collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas,
        )

        return {
            "message": "Document uploaded successfully",
            "filename": file.filename,
            "chunks": len(chunks),
        }

    except HTTPException:
        # Re-raise HTTPExceptions so FastAPI preserves the status code.
        raise
    except Exception as exc:
        # Wrap any unexpected error in a 500 response.
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ask")
async def ask_question(question: Question) -> Dict[str, Any]:
    """
    Answer a user's question using the uploaded documents as context.

    Steps:
    1. Query ChromaDB for the top-k relevant chunks.
    2. Concatenate those chunks into a context block.
    3. Build a prompt and send it to Ollama.
    4. Return the answer plus lightweight source metadata.
    """
    try:
        # Search the vector database for relevant chunks.
        results = collection.query(
            query_texts=[question.question],
            n_results=3,
        )

        documents = results.get("documents") or []
        if not documents or not documents[0]:
            # No chunks have been indexed yet.
            return {
                "answer": "No documents found. Please upload documents first.",
                "sources": [],
            }

        # Combine relevant chunks as a single context string.
        context = "\n\n".join(documents[0])

        # Prompt template instructing the LLM how to behave.
        prompt = f"""You are a helpful study assistant. Answer the question based on the provided context. 
If the answer is not in the context, say so clearly.

Context:
{context}

Question: {question.question}

Answer:"""

        # Get answer from Ollama (with automatic fallback to other models).
        try:
            answer = query_ollama(prompt)
        except Exception as ollama_error:
            # Return a user-friendly error message that the frontend can show directly.
            error_msg = str(ollama_error)

            if "unable to allocate" in error_msg.lower() or "buffer" in error_msg.lower():
                error_msg = (
                    f"⚠️ Memory Error: {error_msg}\n\n"
                    "Quick fixes:\n"
                    "1. Restart Ollama: Close terminal running 'ollama serve', then run it again\n"
                    "2. Free up RAM: Close other applications\n"
                    "3. Try a smaller model: Run 'ollama pull tinyllama' then restart\n"
                    "4. Check available models: Visit http://localhost:8000/models"
                )
            else:
                error_msg = (
                    f"⚠️ Error: {error_msg}\n\nPlease check:\n"
                    "1. Is Ollama running? (Run 'ollama serve' in terminal)\n"
                    "2. Is a model installed? (Run 'ollama pull llama3.2:1b' or 'ollama pull tinyllama')"
                )

            return {
                "answer": error_msg,
                "sources": [],
            }

        # Prepare human-friendly source information from ChromaDB metadata.
        sources: List[Dict[str, Any]] = []
        metadatas = results.get("metadatas") or []
        if metadatas and metadatas[0]:
            sources = [
                {
                    "source": meta.get("source", "Unknown"),
                    "chunk": meta.get("chunk", 0),
                }
                for meta in metadatas[0]
            ]

        return {
            "answer": answer,
            "sources": sources,
        }

    except Exception as exc:
        # Include a traceback in the error to make debugging easier in development.
        import traceback

        error_detail = f"{exc}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail) from exc


@app.delete("/clear")
async def clear_database() -> Dict[str, str]:
    """
    Delete all indexed documents from ChromaDB.

    This recreates the collection from scratch so the app starts with
    an empty vector store again.
    """
    try:
        global collection

        chroma_client.delete_collection(name=COLLECTION_NAME)
        collection = get_or_create_collection()

        return {"message": "Database cleared successfully"}

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# Optional: run the server directly with `python main.py` for local testing.
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)