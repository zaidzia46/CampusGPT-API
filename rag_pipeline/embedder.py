import json
from pathlib import Path

ROOT       = Path(__file__).parent.parent
CHUNKS_DIR = ROOT / "UNIdata" / "chunks"
DB_PATH    = str((ROOT / "UNIdata" / "vectordb").resolve())

COLLECTION_NAME = "cui_sahiwal_kb"
EMBED_MODEL     = "all-MiniLM-L6-v2"
BATCH_SIZE      = 64


def embed(semester: str, wipe: bool = True) -> dict:
    chunk_file = CHUNKS_DIR / f"chunks_{semester}.json"

    if not chunk_file.exists():
        return {
            "success": False,
            "error":   f"No chunk file found for semester '{semester}'. Run generate first.",
        }

    with open(chunk_file, encoding="utf-8") as f:
        data = json.load(f)

    chunks   = data["chunks"]
    log_lines = [f"Loaded {len(chunks)} chunks (semester: {semester})"]

    try:
        import chromadb
        from chromadb.config import Settings
        from sentence_transformers import SentenceTransformer

        client = chromadb.PersistentClient(
            path=DB_PATH,
            settings=Settings(anonymized_telemetry=False),
        )

        if wipe:
            try:
                client.delete_collection(COLLECTION_NAME)
                log_lines.append(f"Wiped existing collection '{COLLECTION_NAME}'")
            except Exception:
                pass

        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        model = SentenceTransformer(EMBED_MODEL)
        log_lines.append(f"Embedding with model: {EMBED_MODEL}")

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
                vecs = model.encode(texts, show_progress_bar=False).tolist()
                collection.upsert(
                    ids=ids,
                    documents=texts,
                    embeddings=vecs,
                    metadatas=metadatas,
                )
                log_lines.append(f"Upserted batch — {i + 1}/{len(chunks)} chunks")
                ids, texts, metadatas = [], [], []

        final_count = collection.count()
        log_lines.append(f"Done. Collection '{COLLECTION_NAME}' now has {final_count} chunks.")

        return {
            "success":     True,
            "semester":    semester,
            "wiped":       wipe,
            "total_embedded": final_count,
            "log":         log_lines,
        }

    except Exception as e:
        log_lines.append(f"[ERROR] {e}")
        return {
            "success": False,
            "error":   str(e),
            "log":     log_lines,
        }