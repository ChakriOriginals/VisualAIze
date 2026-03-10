from __future__ import annotations
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

CHROMA_PATH = Path("./chroma_db")
COLLECTION_NAME = "math_knowledge"

_collection = None

def _get_collection():
    global _collection
    if _collection is not None:
        return _collection
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    _collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )
    return _collection

def retrieve(query: str, n_results: int = 6, min_relevance: float = 0.3) -> List[dict]:
    collection = _get_collection()
    if collection.count() == 0:
        logger.warning("RAG DB empty — run: python -m backend.rag.ingest_data")
        return []
    try:
        n_results = min(n_results, collection.count())
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        docs = []
        for i, doc in enumerate(results["documents"][0]):
            relevance = 1 - results["distances"][0][i]
            if relevance < min_relevance:
                continue
            docs.append({
                "content": doc,
                "metadata": results["metadatas"][0][i],
                "relevance": relevance
            })
        # Sort by relevance descending
        docs.sort(key=lambda x: x["relevance"], reverse=True)
        return docs
    except Exception as e:
        logger.error(f"RAG retrieval error: {e}")
        return []

def retrieve_multi(queries: List[str], n_per_query: int = 3) -> List[dict]:
    """Retrieve using multiple queries, deduplicate results."""
    seen_content = set()
    all_docs = []
    for query in queries:
        docs = retrieve(query, n_results=n_per_query)
        for doc in docs:
            key = doc["content"][:100]
            if key not in seen_content:
                seen_content.add(key)
                all_docs.append(doc)
    all_docs.sort(key=lambda x: x["relevance"], reverse=True)
    return all_docs

def format_context(docs: List[dict], max_chars: int = 2500) -> str:
    if not docs:
        return ""
    parts = []
    total = 0
    for doc in docs:
        meta = doc["metadata"]
        source = meta.get("source", "unknown")
        topic = meta.get("topic", "")
        difficulty = meta.get("difficulty", "")
        relevance = doc["relevance"]
        content = doc["content"].strip()
        entry = f"[{source} | {topic} | {difficulty} | relevance={relevance:.2f}]\n{content}"
        if total + len(entry) > max_chars:
            break
        parts.append(entry)
        total += len(entry)
    return "\n\n---\n\n".join(parts)

def get_db_stats() -> dict:
    collection = _get_collection()
    return {"total_documents": collection.count()}