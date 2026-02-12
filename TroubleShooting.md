# 🛠️ Troubleshooting (Ollama & Local Setup)

This section covers **common issues faced while running Ollama locally**, especially on **Windows**, and how to fix them.

---

## 🔍 Check Installed Ollama Models

If you’re unsure whether any models are installed:

```bash
ollama list
```

Example output:

```
NAME               ID              SIZE      MODIFIED
llama3.2:1b        baf6a787fdff    1.3 GB    9 days ago
llama3.2:latest    a80c4f17acd5    2.0 GB    13 days ago
```

✅ If at least one model appears, Ollama is ready.

---

## ❌ Ollama Not Responding / Backend Cannot Connect

If FastAPI `/health` or `/ask` fails with **connection refused**, Ollama may not be running.

### Check if Ollama processes are running:

```bash
tasklist | findstr ollama
```

Example output:

```
ollama app.exe        12428
ollama.exe              996
```

---

## 🔄 Restart Ollama Cleanly (Recommended Fix)

Sometimes Ollama gets stuck or holds memory.

### 1️⃣ Kill all Ollama processes:

```bash
taskkill /F /T /IM ollama*
```

Expected output:

```
SUCCESS: The process ... has been terminated.
```

### 2️⃣ Confirm Ollama is fully stopped:

```bash
tasklist | findstr ollama
```

➡️ No output means Ollama is fully stopped ✅

### 3️⃣ Restart Ollama:

```bash
ollama serve
```

Leave this terminal open.

---

## 🧠 Model Not Found Error

If you see errors like:

* `model not found`
* `no such model`

Pull the model again:

```bash
ollama pull llama3.2:1b
```

Or use a lighter model (recommended for low RAM):

```bash
ollama pull tinyllama
```

---

## 💾 Memory / Buffer Errors

Common messages:

* `out of memory`
* `buffer allocation failed`
* `failed to allocate tensor`

### Fixes:

* Restart Ollama (steps above)
* Close heavy applications
* Use a smaller model:

  ```bash
  ollama pull tinyllama
  ```
* Update backend default model to a smaller one

---

## 🌐 Ollama API Not Reachable

Ollama runs locally at:

```
http://localhost:11434
```

Test in browser or terminal:

```bash
curl http://localhost:11434/api/tags
```

If this fails:

* Ollama is not running
* Firewall/VPN may be blocking localhost

---

## 🧪 Backend Health Check

Once Ollama is running, test backend:

```bash
http://localhost:8000/health
```

Expected:

* List of installed models
* Ollama connectivity status

---

## 🧹 Reset Everything (Last Resort)

If things get messy:

1. Stop backend (`Ctrl + C`)
2. Kill Ollama processes
3. Restart Ollama:

   ```bash
   ollama serve
   ```
4. Restart backend:

   ```bash
   uvicorn main:app --reload
   ```

---

## ✅ Summary of Useful Ollama Commands

| Purpose               | Command                      |
| --------------------- | ---------------------------- |
| List models           | `ollama list`                |
| Pull model            | `ollama pull llama3.2:1b`    |
| Start Ollama          | `ollama serve`               |
| Check running process | `tasklist \| findstr ollama` |
| Kill Ollama           | `taskkill /F /T /IM ollama*` |

---

## 📌 Tip

If you see **weird behavior**, always try:

> **Kill Ollama → Restart Ollama → Restart Backend**

It fixes 90% of issues.

---
