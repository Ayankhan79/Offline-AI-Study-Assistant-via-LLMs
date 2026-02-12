> ⚠️ **Important note**:
> `python main.py` will **NOT** start FastAPI unless your `main.py` explicitly runs `uvicorn`.
> FastAPI apps are started via **uvicorn**.

---

## ▶️ How to Run the Project (3 Terminals)

### 🖥️ Terminal 1 — Start Ollama (LLM Server)

```bash
ollama serve
```

Make sure at least one model is installed:

```bash
ollama pull llama3.2:1b
# or
ollama pull tinyllama
```

Leave this terminal running.

---

### 🖥️ Terminal 2 — Start Backend (FastAPI)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at:

```
http://localhost:8000
```

---

### 🖥️ Terminal 3 — Start Frontend

```bash
cd frontend
python -m http.server 3000
```

Open in browser:

```
http://localhost:3000/index.html
```

---

## ✅ Corrected vs Your Original Commands

| Your command                 | Status            |
| ---------------------------- | ----------------- |
| `ollama serve`               | ✅ Correct         |
| `python main.py`             | ❌ Needs `uvicorn` |
| `python -m http.server 3000` | ✅ Correct         |

---

## 💡 Optional (If you REALLY want `python main.py`)

If you *insist* on:

```bash
python main.py
```

Then add this at the **bottom of `main.py`**:

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

After that, this will work:

```bash
cd backend
python main.py
```

---

## 🎯 Final Verdict

✔ Your idea is correct
✔ Just needed the FastAPI startup fix
✔ The 3-terminal setup is clean and beginner-friendly
✔ This looks **professional** on GitHub

If you want, I can now:

* Rewrite this as a **very short “Quick Start” section**
* Add **screenshots placeholders** for GitHub
* Add **badges** (Python, FastAPI, Ollama)

Just say the word 😄
