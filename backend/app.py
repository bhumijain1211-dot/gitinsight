"""
app.py
------
The Flask web server. This is the bridge between the React frontend and
our ingest.py / rag_chain.py logic.

Flask basics (since you're new to it):
- @app.route("/some/path", methods=["POST"]) marks a function as the
  handler for requests to that URL.
- request.json gives you the JSON body the frontend sent.
- jsonify(...) converts a Python dict into a JSON response.
- CORS is needed because our React app (e.g. localhost:5173) and this
  Flask app (localhost:5000) run on different ports -- browsers block
  cross-origin requests by default unless the server allows it.
"""

import os
import traceback
from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()  # reads variables from .env into os.environ

from ingest import ingest_repo, VECTORSTORE_DIR
from rag_chain import ask_question

app = Flask(__name__)
CORS(app)  # allow the React dev server to call this API


@app.route("/api/health", methods=["GET"])
def health():
    """Simple check to confirm the server is running."""
    return jsonify({"status": "ok"})


@app.route("/api/ingest", methods=["POST"])
def ingest():
    """
    Body: { "repo_url": "https://github.com/some/repo" }
    Clones + processes the repo, returns a repo_id to use in /api/chat.
    """
    data = request.json or {}
    repo_url = data.get("repo_url")

    if not repo_url:
        return jsonify({"error": "repo_url is required"}), 400

    try:
        result = ingest_repo(repo_url=repo_url)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Body: {
      "repo_id": "psf_requests_a1b2c3",
      "question": "How does the auth module work?",
      "chat_history": [{"question": "...", "answer": "..."}]  // optional
    }
    """
    data = request.json or {}
    repo_id = data.get("repo_id")
    question = data.get("question")
    chat_history = data.get("chat_history", [])

    if not repo_id or not question:
        return jsonify({"error": "repo_id and question are required"}), 400

    try:
        result = ask_question(repo_id, question, chat_history)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/repos", methods=["GET"])
def list_repos():
    """
    Lists repo_ids that have already been ingested (have a vector store
    saved on disk), so the frontend can show them without re-ingesting.
    """
    if not VECTORSTORE_DIR.exists():
        return jsonify({"repos": []})
    repos = [p.name for p in VECTORSTORE_DIR.iterdir() if p.is_dir()]
    return jsonify({"repos": repos})


if __name__ == "__main__":
    # debug=True auto-reloads the server when you save a file -- handy while developing
    app.run(debug=True, port=5000)
