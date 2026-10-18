# GitInsight

A RAG-based conversational assistant that lets you ask questions about any public GitHub repo in plain English.

**Stack:** React (frontend) · Flask (backend API) · LangChain (RAG orchestration) · ChromaDB (vector store) · sentence-transformers (embeddings, free/local) · Groq (LLM, free tier)

---

## How it works

1. You paste a GitHub repo URL.
2. The backend clones it, breaks the code into chunks, and turns each chunk into an embedding (a vector of numbers representing its meaning), stored in ChromaDB.
3. When you ask a question, the backend finds the most relevant chunks, stuffs them into a prompt, and asks Groq's LLM to answer using that context.
4. The frontend shows the answer plus which files it came from.

---

## Setup

### 1. Get a free Groq API key
Go to https://console.groq.com/keys and create a key.

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# open .env and paste your GROQ_API_KEY

python app.py
```

The API now runs at `http://localhost:5000`. Test it: open `http://localhost:5000/api/health` in your browser — you should see `{"status": "ok"}`.

### 3. Frontend

In a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

Open the URL it prints (usually `http://localhost:5173`).

### 4. Use it

1. Paste a small public repo URL first to test, e.g. `https://github.com/pallets/flask` (big repos take longer to ingest since everything runs locally).
2. Click "Ingest Repo" — wait for it to finish (cloning + embedding takes a bit).
3. Ask questions like "What does the routing decorator do?" or "Where is the main entry point?".

---

## Project structure

```
gitinsight/
├── backend/
│   ├── app.py          # Flask routes (the API)
│   ├── ingest.py        # Clone repo -> chunk -> embed -> store in Chroma
│   ├── rag_chain.py      # Retrieval + Groq LLM -> generates answers
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx              # Switches between RepoInput and Chat screens
    │   ├── components/
    │   │   ├── RepoInput.jsx    # Paste-a-URL screen
    │   │   └── Chat.jsx         # Chat UI
    │   └── index.css
    └── package.json
```

---

## Common issues

- **"No module named flask_cors"** → re-run `pip install -r requirements.txt` inside the venv.
- **CORS errors in browser console** → make sure `app.py` is actually running on port 5000.
- **Ingestion is slow** → embeddings run locally on CPU by default; first run also downloads the embedding model (~90MB), which only happens once.
- **Groq errors about model name** → check https://console.groq.com/docs/models for current available model names, they change occasionally.

---

## Ideas to extend this (good for your resume too)

- Add re-ranking (e.g. a cross-encoder) after retrieval for better accuracy.
- Support uploading a local zip folder, not just public GitHub URLs.
- Add authentication so multiple users can have their own ingested repos.
- Show actual code snippets (not just filenames) in the "sources" section.
- Deploy: Flask backend to Render/Railway, React frontend to Vercel/Netlify.
