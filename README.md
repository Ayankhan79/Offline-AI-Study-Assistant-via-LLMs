## AI Study Assistant

An **offline-first AI study assistant** that lets you upload PDFs (notes, textbooks, slides) and then **ask natural-language questions** about them.  
All processing happens **locally on your machine** using **FastAPI**, **ChromaDB** for vector search, and **Ollama** for running LLMs.

---

### Features

- **PDF ingestion & text extraction**
  - Upload any PDF from the frontend.
  - Backend extracts text with `PyPDF2` and splits it into overlapping chunks for better semantic search.
- **Semantic search with ChromaDB**
  - Chunks are stored in a local ChromaDB collection (`study_docs`) with SentenceTransformer embeddings (`all-MiniLM-L6-v2`).
  - Queries search this collection to find the most relevant chunks.
- **Local LLM question answering (via Ollama)**
  - Relevant chunks are sent as context to an Ollama model (default `llama3.2:1b`).
  - Automatic fallback through several models if one fails (`llama3.2:1b`, `llama3.2`, `llama3:1b`, `tinyllama`, `phi`).
- **Beautiful single-page frontend**
  - Modern glassmorphism UI built in plain HTML/CSS/JS.
  - Drag-and-drop-style upload, live stats (docs/chunks/questions), chat-style Q&A view, and source citations.
- **Local & private**
  - All PDFs and embeddings stay on your machine.
  - No external cloud services required beyond Ollama running locally.

---

### Project Structure

- `backend/`
  - `main.py` – FastAPI app with:
    - PDF upload endpoint and text extraction.
    - ChromaDB initialization / collection management.
    - Question answering endpoint that:
      - Retrieves top relevant chunks from ChromaDB.
      - Builds a prompt and calls Ollama.
      - Returns an answer plus document/chunk sources.
    - Health/model listing endpoints.
    - Clear-database endpoint.
    - Well-structured helpers and docstrings so the code is easy to read and extend.
  - `pyproject.toml` / `uv.lock` – Python project and dependency metadata (for `uv` / `pip` style workflows).
- `frontend/`
  - `index.html` – Markup-only single-page shell:
    - Premium landing/hero section.
    - PDF upload panel.
    - Session document list.
    - Chat-style Q&A area wired to the backend via `fetch`.
    - References the external CSS/JS files below.
  - `styles.css` – All UI styling (glassmorphism layout, typography, responsive design).
  - `app.js` – Vanilla JS logic for upload, stats, chat, and API calls.

---

### Backend Overview (`backend/main.py`)

- **Tech stack**
  - FastAPI
  - ChromaDB (`chromadb`)
  - SentenceTransformer embeddings (`all-MiniLM-L6-v2`)
  - PyPDF2 (PDF parsing)
  - Requests (HTTP calls to Ollama)
  - Uvicorn (development server)

- **Key components**
  - **App & CORS setup**
    - Creates a FastAPI app and enables permissive CORS so the browser frontend (served from `file://` or any host) can call the API.
  - **ChromaDB collection**
    - On startup, tries to get or create a collection named `study_docs` using the SentenceTransformer embedding function.
  - **Data model**
    - `Question` (`pydantic.BaseModel`) with a single `question: str` field for the `/ask` endpoint.
  - **Helpers**
    - `extract_text_from_pdf(pdf_file)` – reads the bytes of a PDF and concatenates text from all pages.
    - `chunk_text(text, chunk_size=1000, overlap=200)` – splits raw text into overlapping chunks to improve retrieval quality.
    - `get_available_models()` – queries `http://localhost:11434/api/tags` from Ollama and returns a list of installed models.
    - `query_ollama(prompt, model="llama3.2:1b", fallback_models=[...])` – sends a non-streaming generation request to Ollama, with:
      - Retry/fallback over multiple models.
      - Handling for memory/buffer errors.
      - Helpful suggestions if all models fail.

- **HTTP endpoints**
  - `GET /`
    - Simple “API is running” message.
  - `GET /health`
    - Checks connectivity to Ollama.
    - Returns list of models and flags for default model availability and small recommended models.
  - `GET /models`
    - Returns detailed info on all installed Ollama models (name, size, modified).
  - `POST /upload`
    - Accepts a PDF file (`UploadFile`).
    - Extracts text and chunks it.
    - Adds chunks to ChromaDB with:
      - `ids`: `<filename>_<chunk_index>`
      - `metadatas`: `{"source": filename, "chunk": index}`
    - Returns filename and total chunks stored.
  - `POST /ask`
    - Accepts JSON `{ "question": "..." }`.
    - Queries ChromaDB for top `n_results=3` chunks.
    - Builds a prompt including the context and question for Ollama.
    - Calls `query_ollama` and returns:
      - `answer`: model output (or a human-readable error string).
      - `sources`: list of `{ source, chunk }` records for transparency.
  - `DELETE /clear`
    - Deletes the `study_docs` collection and recreates it empty.
    - Returns a simple success message.

---

### Frontend Overview (`frontend/index.html`, `styles.css`, `app.js`)

- **Pure HTML/CSS/JS**
  - No framework required; everything is client-side vanilla JavaScript.
  - The frontend is now split into:
    - `index.html` (structure/markup),
    - `styles.css` (styling),
    - `app.js` (behavior and API calls).

- **Layout**
  - **Hero / marketing section**
    - Branding, navigation, short explanation of how it works.
    - Buttons to jump to the app or trigger PDF upload.
  - **Stats bar**
    - Live counters for:
      - Documents uploaded.
      - Chunks indexed.
      - Questions asked.
      - System status (Ready / Uploading / Thinking / Error / Offline).
  - **Study workspace**
    - **Upload panel**
      - `input[type="file"]` (hidden) plus a styled “Choose PDF File” button.
      - Shows upload status and session document list.
      - “Clear all documents” button calls the backend `/clear` endpoint.
    - **Chat panel**
      - Scrollable message area for Q&A.
      - Input box and “Ask” button, also bound to Enter key.

- **Key JS functions**
  - `uploadFile(event)`
    - Sends selected PDF to `POST {API_URL}/upload`.
    - Updates status, stats, and “Documents this session” list.
  - `askQuestion()`
    - Sends a question to `POST {API_URL}/ask`.
    - Displays the question and then the answer (with sources, if present).
  - `clearDatabase()`
    - Confirms with the user, then calls `DELETE {API_URL}/clear`.
    - Clears chat and resets stats/document list.
  - `syncStats()`, `setStatusBadge()`
    - Keep the on-screen counters and status label in sync.

---

### Prerequisites

- **System**
  - Python 3.10+ (recommended)
  - Node not required (frontend is static HTML).
- **Ollama**
  - Install Ollama from the official site (`ollama.ai`).
  - Make sure you can run `ollama serve` and `ollama run llama3.2:1b` (or another model).
  - Pull at least one supported model, e.g.:
    - `ollama pull llama3.2:1b`
    - or a smaller one like `ollama pull tinyllama`

---

### Backend Setup & Run

From the `backend` directory:

```bash
# (Recommended) use uv or a virtual environment; examples:
# Using uv:
uv sync

# Or using plain pip + venv (if you prefer)
python -m venv .venv
.venv\Scripts\activate   # on Windows
pip install -r requirements.txt  # if you export deps, or mimic pyproject

# Start FastAPI with uvicorn (dev)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Make sure **Ollama is running** in a separate terminal:

```bash
ollama serve
```

You can verify the API is working:

- `GET http://localhost:8000/` – basic “API is running” JSON.
- `GET http://localhost:8000/health` – checks Ollama connectivity and lists models.

---

### Frontend Setup & Run

The frontend lives in three files (`index.html`, `styles.css`, `app.js`):

- Option 1: Open `frontend/index.html` directly in your browser (double-click or “Open with…”).
- Option 2: Serve it with any static file server (optional, nicer for CORS):

```bash
cd frontend
python -m http.server 5500
```

Then open `http://localhost:5500/index.html` in your browser.

> **Important**: The frontend expects the backend at `http://localhost:8000`.  
> Make sure the FastAPI server is running there, or adjust `API_URL` in `app.js` if you change the port.

---

### Typical Usage Flow

1. **Start Ollama**
   - Run `ollama serve` in a terminal.
   - Ensure at least one model (e.g. `llama3.2:1b` or `tinyllama`) is pulled.
2. **Start the backend**
   - From `backend`, run `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`.
3. **Open the frontend**
   - Open `frontend/index.html` in your browser (or via a static server).
4. **Upload PDFs**
   - Click “Choose PDF File”, select your study material.
   - Wait for the success message and chunk count.
5. **Ask questions**
   - Type questions in the input box and press Enter or click “Ask”.
   - Answers appear in the chat with source references (document + chunk numbers).
6. **Reset**
   - Use “Clear all documents” to wipe the vector store and start fresh.

---

### Error Handling & Troubleshooting

- **Cannot connect to Ollama**
  - Backend `/health` and `/ask` can return messages suggesting:
    - Start Ollama: `ollama serve`.
    - Install a model: `ollama pull llama3.2:1b` or `ollama pull tinyllama`.
- **Memory / buffer errors**
  - The backend detects common memory errors from Ollama and responds with:
    - Tips to restart Ollama.
    - Suggestions to free up RAM or use a smaller model.
- **Frontend shows “Offline” or “Error”**
  - Confirm backend is running on port `8000`.
  - Check the browser console / network tab to see failing requests.
  - Use `/health` and `/models` endpoints directly in a browser or tool like curl/Postman.

---

### Customization Ideas

- Swap out the default Ollama model or adjust the model fallback order.
- Tune chunk sizes and overlap in `chunk_text()` for different document types.
- Add user accounts and per-user collections in ChromaDB.
- Persist document metadata or upload history in a separate database.
- Extend the frontend with:
  - Highlighting for cited snippets.
  - Dark/light theme toggle.
  - Per-document filtering of questions.

---

### License

Add your preferred license here (e.g. MIT, Apache-2.0).