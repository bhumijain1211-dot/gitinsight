# GitInsight

Ask questions about any public GitHub repository in plain English. GitInsight indexes a repo's code and uses retrieval-augmented generation (RAG) to answer with the relevant files cited.

<!-- Add a screenshot here: ![GitInsight screenshot](screenshot.png) -->

## Features

- **Repository ingestion:** paste a GitHub URL; the backend clones, parses, chunks, and indexes the code.
- **Semantic search:** code chunks are embedded and retrieved by meaning, not just keywords.
- **Grounded answers:** the LLM answers using only the retrieved code, and says so when the context isn't enough.
- **Source attribution:** every answer lists the files it was drawn from.
- **Conversational memory:** follow-up questions work in context.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite |
| Backend | Flask, Flask-CORS |
| RAG orchestration | LangChain |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`, runs locally) |
| Vector store | ChromaDB (persisted to disk, one store per repo) |
| LLM | Groq (`openai/gpt-oss-120b`) |

## How it works

```
GitHub URL
   │
   ▼
Clone repo ──► Filter files ──► Chunk (1000 chars, 150 overlap)
                                      │
                                      ▼
                          Embed chunks (MiniLM) ──► ChromaDB
                                                       │
Question ──► Embed question ──► Top-5 similar chunks ──┘
                                      │
                                      ▼
                    Prompt (chunks + chat history + question)
                                      │
                                      ▼
                         Groq LLM ──► Answer + source files
```

1. **Ingestion** (`ingest.py`): clones the repo, skips non-code files and folders like `node_modules`, splits files into overlapping chunks, embeds them, and stores them in ChromaDB in batches.
2. **Retrieval** (`rag_chain.py`): the question is embedded and the 5 most similar chunks are fetched.
3. **Generation:** the chunks, chat history, and question go into a prompt that instructs the model to answer only from the provided code.
4. **API** (`app.py`): Flask exposes ingestion and chat endpoints to the React frontend.

## Getting started

**Prerequisites:** Python 3.10+, Node.js 18+, and a free [Groq API key](https://console.groq.com/keys).

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Create a file named `.env` inside `backend/`:

```
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

Then start the server:

```bash
python app.py
```

The API runs at `http://localhost:5000`. Check `http://localhost:5000/api/health`; it should return `{"status": "ok"}`.

### Frontend

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`, paste a repo URL (try `https://github.com/pallets/flask`), run the ingestion, and start asking questions.

> The first ingestion downloads the embedding model (~90 MB) once, and larger repos take longer since embeddings run on your machine.

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/ingest` | Body: `{ "repo_url": "..." }`. Indexes a repo, returns `repo_id` |
| POST | `/api/chat` | Body: `{ "repo_id", "question", "chat_history" }`. Returns answer and sources |
| GET | `/api/repos` | Lists already-indexed repos |

## Project structure

```
gitinsight/
├── backend/
│   ├── app.py            # Flask routes
│   ├── ingest.py         # Clone → chunk → embed → store
│   ├── rag_chain.py      # Retrieval + Groq LLM chain
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── index.css
        └── components/
            ├── RepoInput.jsx   # Repo URL screen
            └── Chat.jsx        # Chat interface
```

## Current limitations

- Only public GitHub repositories are supported.
- Chunking is character-based, not syntax-aware.
- Indexed data is stored on local disk and has no authentication.

## Roadmap

- Syntax-aware chunking (split by function/class)
- Re-ranking retrieved chunks for better accuracy
- Streaming responses
- Showing code snippets alongside source file names
- Local folder upload
