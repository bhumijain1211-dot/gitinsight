"""
ingest.py
---------
This file is responsible for turning a GitHub repo (or a local folder) into
a searchable "vector store" that our RAG chain can query later.

Think of it as: Repo -> Files -> Chunks -> Embeddings -> Chroma DB (on disk)
"""

import os
import shutil
import hashlib
from pathlib import Path

import git  # from GitPython, lets us clone repos
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
REPOS_DIR = DATA_DIR / "repos"        # where we clone/store raw repo files
VECTORSTORE_DIR = DATA_DIR / "vectorstores"  # where Chroma DBs live, one per repo

REPOS_DIR.mkdir(parents=True, exist_ok=True)
VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

# Only ingest files with these extensions (source code + docs).
# Skips images, binaries, lockfiles, etc.
ALLOWED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb", ".php",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rs", ".swift", ".kt",
    ".md", ".txt", ".json", ".yaml", ".yml", ".html", ".css",
}

# Folders we never want to walk into
IGNORED_DIRS = {
    ".git", "node_modules", "__pycache__", "venv", ".venv",
    "dist", "build", ".next", "target", "vendor", ".idea", ".vscode",
}

# Loaded once and reused -- this is the model that turns text into embeddings.
# "all-MiniLM-L6-v2" is small, fast, free, and runs locally (no API key needed).
_embeddings = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings


def repo_id_from_url(repo_url: str) -> str:
    """
    Turns a repo URL into a short, filesystem-safe ID, e.g.
    'https://github.com/psf/requests' -> 'psf_requests_a1b2c3'
    We hash it so the same repo always maps to the same folder.
    """
    name_part = repo_url.rstrip("/").split("/")[-2:]
    safe_name = "_".join(name_part).replace(".git", "")
    short_hash = hashlib.sha1(repo_url.encode()).hexdigest()[:6]
    return f"{safe_name}_{short_hash}"


def clone_repo(repo_url: str, repo_id: str) -> Path:
    """
    Clones a public GitHub repo to REPOS_DIR/<repo_id>.
    If it's already cloned, reuses it (so re-ingesting is fast).
    """
    dest = REPOS_DIR / repo_id
    if dest.exists():
        return dest
    git.Repo.clone_from(repo_url, dest, depth=1)  # depth=1 = only latest commit, faster
    return dest


def save_uploaded_folder(uploaded_path: Path, repo_id: str) -> Path:
    """
    For the 'upload a folder' path: just copy it into our repos dir
    under a consistent repo_id so the rest of the pipeline is identical.
    """
    dest = REPOS_DIR / repo_id
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(uploaded_path, dest)
    return dest


def load_documents(repo_path: Path):
    """
    Walks the repo folder and loads every allowed file's text content
    into a LangChain Document (which is just text + metadata like filename).
    """
    documents = []
    for root, dirs, files in os.walk(repo_path):
        # Skip ignored directories in-place so os.walk doesn't descend into them
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for filename in files:
            file_path = Path(root) / filename
            if file_path.suffix not in ALLOWED_EXTENSIONS:
                continue
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if not text.strip():
                continue

            relative_path = str(file_path.relative_to(repo_path))
            documents.append(
                Document(page_content=text, metadata={"source": relative_path})
            )
    return documents


def chunk_documents(documents):
    """
    Splits each file's text into smaller overlapping chunks.
    Why chunk? Because:
      1. Embedding models have a max input size.
      2. Smaller chunks = more precise retrieval (you get the exact
         function/section relevant to the question, not the whole file).

    We use a generic recursive splitter that tries to break on natural
    boundaries (blank lines, then lines, then words) so code doesn't get
    cut in a weird spot as often.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,      # ~1000 characters per chunk
        chunk_overlap=150,    # overlap so context isn't lost at chunk boundaries
        separators=["\n\n", "\n", " ", ""],
    )
    return splitter.split_documents(documents)


def ingest_repo(repo_url: str = None, uploaded_path: Path = None) -> dict:
    """
    Main entry point. Either pass a repo_url (to clone) or an uploaded_path
    (a folder already on disk). Returns info about the ingested repo.
    """
    if not repo_url and not uploaded_path:
        raise ValueError("Provide either repo_url or uploaded_path")

    source_label = repo_url if repo_url else str(uploaded_path)
    repo_id = repo_id_from_url(source_label)

    if repo_url:
        repo_path = clone_repo(repo_url, repo_id)
    else:
        repo_path = save_uploaded_folder(uploaded_path, repo_id)

    documents = load_documents(repo_path)
    if not documents:
        raise ValueError("No readable source files found in this repo.")

    chunks = chunk_documents(documents)

    persist_dir = str(VECTORSTORE_DIR / repo_id)

    # Chroma has a max batch size for how many chunks can be added at once
    # (varies by version, commonly ~166). Large repos can easily produce
    # more chunks than that, so we insert in smaller batches instead of
    # all at once.
    BATCH_SIZE = 100
    embeddings = get_embeddings()

    vectordb = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        vectordb.add_documents(batch)

    vectordb.persist()

    return {
        "repo_id": repo_id,
        "num_files": len(documents),
        "num_chunks": len(chunks),
        "persist_dir": persist_dir,
    }


def load_vectorstore(repo_id: str) -> Chroma:
    """
    Reloads an already-ingested repo's vector store from disk,
    so we don't have to re-embed everything on every chat message.
    """
    persist_dir = str(VECTORSTORE_DIR / repo_id)
    if not Path(persist_dir).exists():
        raise ValueError(f"No ingested repo found for id '{repo_id}'")
    return Chroma(persist_directory=persist_dir, embedding_function=get_embeddings())