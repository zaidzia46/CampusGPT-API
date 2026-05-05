"""
rag_pipeline/embedder.py
-------------------------
Embeds chunks into ChromaDB.
- Model and client are cached at module level for performance
- Uses temp collection strategy to prevent data loss on failure
"""

import json
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

ROOT       = Path(__file__).parent.parent
CHUNKS_DIR = ROOT / "UNIdata" / "chunks"
DB_PATH    = str((ROOT / "UNIdata" / "vectordb").resolve())

COLLECTION_NAME      = "cui_sahiwal_kb"
COLLECTION_NAME_TEMP = "cui_sahiwal_kb_temp"
EMBED_MODEL          = "all-MiniLM-L6-v2"
BATCH_SIZE           = 64

# ── Module-level cache — loaded ONCE when server starts ───────────────────
print("[Embedder] Loading SentenceTransformer model...")
_model  = SentenceTransformer(EMBED_MODEL)
_client = chromadb.PersistentClient(
    path=DB_PATH,
    settings=Settings(anonymized_telemetry=False),
)
print("[Embedder] Model and ChromaDB client ready.")


def embed(semester: str, wipe: bool = True) -> dict:
    """
    Embed chunks for the given semester into ChromaDB.

    Strategy:
    1. Embed into a temp collection first
    2. Only if successful → swap temp to real collection
    3. If failed → real collection untouched
    """
    chunk_file = CHUNKS_DIR / f"chunks_{semester}.json"

    if not chunk_file.exists():
        return {
            "success": False,
            "error":   f"No chunk file found for semester '{semester}'. Run generate first.",
            "log":     [],
        }

    with open(chunk_file, encoding="utf-8") as f:
        data = json.load(f)

    chunks    = data["chunks"]
    log_lines = [f"Loaded {len(chunks)} chunks (semester: {semester})"]

    try:
        # ── Step 1: Clean up any leftover temp collection ─────────────
        try:
            _client.delete_collection(COLLECTION_NAME_TEMP)
        except Exception:
            pass

        # ── Step 2: Embed into TEMP collection ────────────────────────
        temp_collection = _client.get_or_create_collection(
            name=COLLECTION_NAME_TEMP,
            metadata={"hnsw:space": "cosine"},
        )
        log_lines.append("Embedding into temp collection...")

        ids, texts, metadatas = [], [], []

        for i, chunk in enumerate(chunks):
            ids.append(chunk["chunk_id"])
            texts.append(chunk["text"])
            metadatas.append({
                k: (str(v) if not isinstance(v, (str, int, float, bool)) else v)
                for k, v in chunk["metadata"].items()
                if v is not None
            })

            if len(ids) == BATCH_SIZE or i == len(chunks) - 1:
                vecs = _model.encode(texts, show_progress_bar=False).tolist()
                temp_collection.upsert(
                    ids=ids,
                    documents=texts,
                    embeddings=vecs,
                    metadatas=metadatas,
                )
                log_lines.append(f"Upserted batch — {i + 1}/{len(chunks)} chunks")
                ids, texts, metadatas = [], [], []

        # ── Step 3: Verify temp collection ────────────────────────────
        temp_count = temp_collection.count()
        if temp_count != len(chunks):
            raise Exception(
                f"Temp collection has {temp_count} chunks, expected {len(chunks)}. Aborting swap."
            )

        log_lines.append(f"Temp collection verified: {temp_count} chunks")

        # ── Step 4: Swap temp → real (only now wipe real collection) ──
        if wipe:
            try:
                _client.delete_collection(COLLECTION_NAME)
                log_lines.append(f"Wiped existing collection '{COLLECTION_NAME}'")
            except Exception:
                pass

        # Recreate real collection and copy from temp
        real_collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        # Get all data from temp and upsert into real
        all_data = temp_collection.get(include=["documents", "embeddings", "metadatas"])

        batch_size = BATCH_SIZE
        total      = len(all_data["ids"])

        for start in range(0, total, batch_size):
            end = min(start + batch_size, total)
            real_collection.upsert(
                ids        = all_data["ids"][start:end],
                documents  = all_data["documents"][start:end],
                embeddings = all_data["embeddings"][start:end],
                metadatas  = all_data["metadatas"][start:end],
            )

        # ── Step 5: Clean up temp collection ──────────────────────────
        _client.delete_collection(COLLECTION_NAME_TEMP)
        log_lines.append("Temp collection cleaned up")

        final_count = real_collection.count()
        log_lines.append(
            f"Done. Collection '{COLLECTION_NAME}' now has {final_count} chunks."
        )

        return {
            "success":        True,
            "semester":       semester,
            "wiped":          wipe,
            "total_embedded": final_count,
            "log":            log_lines,
        }

    except Exception as e:
        log_lines.append(f"[ERROR] {e}")
        # Clean up temp collection on failure
        try:
            _client.delete_collection(COLLECTION_NAME_TEMP)
            log_lines.append("Temp collection cleaned up after failure")
        except Exception:
            pass
        return {
            "success": False,
            "error":   str(e),
            "log":     log_lines,
        }