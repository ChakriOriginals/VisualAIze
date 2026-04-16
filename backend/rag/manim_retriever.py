from __future__ import annotations
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

CHROMA_PATH = Path("./chroma_db")
MANIM_COLLECTION = "manim_examples_v2"  # v2 forces re-ingest with new examples
_manim_collection = None


def _get_manim_collection():
    global _manim_collection
    if _manim_collection is not None:
        return _manim_collection
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    _manim_collection = client.get_or_create_collection(
        name=MANIM_COLLECTION,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )
    return _manim_collection


def ingest_manim_examples():
    """Ingest all curated Manim examples into ChromaDB."""
    from backend.rag.manim_examples import MANIM_EXAMPLES
    collection = _get_manim_collection()
    if collection.count() >= len(MANIM_EXAMPLES):
        logger.info("Manim examples already ingested (%d examples)", collection.count())
        return

    # Clear and re-ingest to ensure freshness
    if collection.count() > 0:
        collection.delete(ids=collection.get()["ids"])

    documents, metadatas, ids = [], [], []
    for i, ex in enumerate(MANIM_EXAMPLES):
        # Rich document: description + tags + code
        # This makes semantic search find examples by concept, not just syntax
        content = (
            f"TOPIC: {ex['topic']}\n"
            f"DESCRIPTION: {ex['description']}\n"
            f"USE FOR: {', '.join(ex['tags'])}\n\n"
            f"CODE PATTERN:\n{ex['code']}"
        )
        documents.append(content)
        metadatas.append({
            "topic": ex["topic"],
            "description": ex["description"],
            "tags": ", ".join(ex["tags"])
        })
        ids.append(f"manim_v2_{i}")

    # Batch add
    BATCH = 50
    for i in range(0, len(documents), BATCH):
        collection.add(
            documents=documents[i:i+BATCH],
            metadatas=metadatas[i:i+BATCH],
            ids=ids[i:i+BATCH]
        )

    logger.info("Ingested %d Manim examples into ChromaDB", len(documents))


def retrieve_manim_examples(query: str, n_results: int = 4) -> List[dict]:
    """
    Retrieve relevant Manim code examples for a given animation query.
    Uses semantic search — finds examples by CONCEPT, not just keyword match.
    """
    collection = _get_manim_collection()
    if collection.count() == 0:
        logger.warning("Manim examples DB empty — ingesting now...")
        ingest_manim_examples()

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
            if relevance > 0.2:  # threshold: only include relevant examples
                docs.append({
                    "content": doc,
                    "topic": results["metadatas"][0][i]["topic"],
                    "description": results["metadatas"][0][i]["description"],
                    "relevance": relevance
                })
        return sorted(docs, key=lambda x: x["relevance"], reverse=True)
    except Exception as e:
        logger.error("Manim RAG retrieval error: %s", e)
        return []


def retrieve_for_scene(scene_titles: List[str], math_topic: str, n_results: int = 5) -> List[dict]:
    """
    Smart multi-query retrieval: searches by topic AND scene types.
    Deduplicates results across queries.
    """
    queries = [
        math_topic,                              # main topic
        f"{math_topic} diagram visualization",   # visual aspect
        " ".join(scene_titles[:2]),              # scene titles
        "equation reveal caption transition",    # always useful patterns
    ]

    seen = set()
    all_docs = []
    for query in queries:
        docs = retrieve_manim_examples(query, n_results=3)
        for doc in docs:
            key = doc["topic"]
            if key not in seen:
                seen.add(key)
                all_docs.append(doc)

    # Always include the scene template and transition
    must_have = ["scene_structure_template", "side_by_side_comparison"]
    existing_topics = {d["topic"] for d in all_docs}
    for must in must_have:
        if must not in existing_topics:
            extra = retrieve_manim_examples(must, n_results=1)
            all_docs.extend(extra)

    return sorted(all_docs, key=lambda x: x["relevance"], reverse=True)[:n_results]


def format_manim_context(docs: List[dict], max_chars: int = 4000) -> str:
    """Format retrieved examples into a prompt-ready string with generalization hints."""
    from backend.rag.manim_examples import GENERALIZATION_RULES

    if not docs:
        return GENERALIZATION_RULES  # always include rules even without examples

    parts = [GENERALIZATION_RULES, "\n\nRELEVANT CODE EXAMPLES TO ADAPT:\n"]
    total = len(GENERALIZATION_RULES)

    for doc in docs:
        entry = (
            f"\n{'='*50}\n"
            f"EXAMPLE: {doc['topic']} (relevance={doc['relevance']:.2f})\n"
            f"USE WHEN: {doc['description']}\n"
            f"{'='*50}\n"
            f"{doc['content']}\n"
        )
        if total + len(entry) > max_chars:
            break
        parts.append(entry)
        total += len(entry)

    return "".join(parts)