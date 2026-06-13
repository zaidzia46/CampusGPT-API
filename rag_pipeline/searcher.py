"""
rag_pipeline/searcher.py
-------------------------
Searches ChromaDB for relevant chunks.
- Model and client cached at module level for performance
"""

from pathlib import Path

import chromadb
from chromadb.config import Settings
from rag_pipeline.model import model as _model

ROOT            = Path(__file__).parent.parent
DB_PATH         = str((ROOT / "UNIdata" / "vectordb").resolve())
COLLECTION_NAME = "cui_sahiwal_kb"

_client = chromadb.PersistentClient(
    path=DB_PATH,
    settings=Settings(anonymized_telemetry=False),
)
print("[Searcher] ChromaDB client ready.")


def search(query: str, top_k: int = 3) -> dict:
    """
    Search ChromaDB for chunks matching the query.
    Returns list of hits with chunk_id, text, distance, metadata.
    """
    try:
        collection = _client.get_collection(COLLECTION_NAME)
        vector     = _model.encode(query).tolist()
        results    = collection.query(
            query_embeddings=[vector],
            n_results=top_k,
        )

        hits = []
        for i in range(len(results["ids"][0])):
            hits.append({
                "chunk_id": results["ids"][0][i],
                "text":     results["documents"][0][i],
                "distance": round(results["distances"][0][i], 4),
                "metadata": results["metadatas"][0][i],
            })

        return {"success": True, "query": query, "results": hits}

    except Exception as e:
        return {"success": False, "error": str(e), "results": []}
