"""
rag_chain.py
------------
This connects the vector store from ingest.py to an LLM (Groq) so we can
actually answer questions about a repo.

Flow for one question:
  question -> retriever finds top-k relevant chunks -> those chunks + the
  question + chat history get put into a prompt -> Groq LLM generates an
  answer -> we return the answer and which files it came from.
"""

import os
from langchain_groq import ChatGroq
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

from ingest import load_vectorstore

# This system prompt tells the LLM HOW to behave: answer using the provided
# code context, admit when it doesn't know, and reference filenames.
QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are GitInsight, an assistant that answers questions about a
specific GitHub repository using ONLY the code context provided below.

- If the answer isn't in the context, say you don't have enough information
  from the retrieved code, rather than guessing.
- When relevant, mention which file(s) the answer comes from.
- Keep answers concise and technical.

Context from the repository:
{context}

Question: {question}

Answer:""",
)


def get_llm():
    """
    Creates the Groq LLM client. GROQ_API_KEY must be set in your .env file.
    llama-3.3-70b-versatile is a good default: fast and capable for code Q&A.
    """
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=0.2,  # low temperature = more focused/factual, less creative
    )


def build_chain(repo_id: str, chat_history: list = None):
    """
    Builds a ConversationalRetrievalChain for a specific repo.

    - retriever: searches the repo's vector store for the most relevant
      chunks to a given question (k=5 means "top 5 matches").
    - memory: keeps track of chat history so follow-up questions like
      "what about the login function?" after "explain auth" still work.
    """
    vectordb = load_vectorstore(repo_id)
    retriever = vectordb.as_retriever(search_kwargs={"k": 5})

    memory = ConversationBufferMemory(
        memory_key="chat_history", return_messages=True, output_key="answer"
    )
    # Pre-load any prior turns passed in from the frontend
    if chat_history:
        for turn in chat_history:
            memory.chat_memory.add_user_message(turn["question"])
            memory.chat_memory.add_ai_message(turn["answer"])

    chain = ConversationalRetrievalChain.from_llm(
        llm=get_llm(),
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": QA_PROMPT},
    )
    return chain


def ask_question(repo_id: str, question: str, chat_history: list = None) -> dict:
    """
    The main function app.py will call. Returns the answer plus the
    filenames of chunks used, so the frontend can show "sources".
    """
    chain = build_chain(repo_id, chat_history)
    result = chain.invoke({"question": question})

    sources = sorted({
        doc.metadata.get("source", "unknown")
        for doc in result.get("source_documents", [])
    })

    return {
        "answer": result["answer"],
        "sources": sources,
    }
