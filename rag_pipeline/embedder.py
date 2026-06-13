import gc
import json
from pathlib import Path

import chromadb
from chromadb.config import Settings

ROOT       = Path(__file__).parent.parent
CHUNKS_DIR = ROOT / "UNIdata" / "chunks"
DB_PATH    = str((ROOT / "UNIdata" / "vectordb").resolve())

COLLECTION_NAME      = "cui_sahiwal_kb"
COLLECTION_NAME_TEMP = "cui_sahiwal_kb_temp"
BATCH_SIZE           = 16

# NO module-level model or client here anymore


def embed(semester: str, wipe: bool = True) -> dict:
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

    # load model and client INSIDE the function — not at startup
    local_model  = None
    local_client = None

    try:
        from sentence_transformers import SentenceTransformer

        log_lines.append("Loading embedding model...")
        local_model = SentenceTransformer("all-MiniLM-L6-v2")
        log_lines.append("Model loaded.")

        local_client = chromadb.PersistentClient(
            path=DB_PATH,
            settings=Settings(anonymized_telemetry=False),
        )

        # ── Step 1: Clean up any leftover temp collection ─────────────
        try:
            local_client.delete_collection(COLLECTION_NAME_TEMP)
        except Exception:
            pass

        # ── Step 2: Embed into TEMP collection ────────────────────────
        temp_collection = local_client.get_or_create_collection(
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
                vecs = local_model.encode(texts, show_progress_bar=False).tolist()
                temp_collection.upsert(
                    ids=ids,
                    documents=texts,
                    embeddings=vecs,
                    metadatas=metadatas,
                )
                log_lines.append(f"Upserted batch — {i + 1}/{len(chunks)} chunks")
                ids, texts, metadatas = [], [], []
                gc.collect()    # ← free memory after every batch

        # ── Step 3: Verify temp collection ────────────────────────────
        temp_count = temp_collection.count()
        if temp_count != len(chunks):
            raise Exception(
                f"Temp collection has {temp_count} chunks, expected {len(chunks)}. Aborting swap."
            )
        log_lines.append(f"Temp collection verified: {temp_count} chunks")

        # ── Step 4: Swap temp → real ───────────────────────────────────
        if wipe:
            try:
                local_client.delete_collection(COLLECTION_NAME)
                log_lines.append(f"Wiped existing collection '{COLLECTION_NAME}'")
            except Exception:
                pass

        real_collection = local_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        all_data   = temp_collection.get(include=["documents", "embeddings", "metadatas"])
        total      = len(all_data["ids"])

        for start in range(0, total, BATCH_SIZE):
            end = min(start + BATCH_SIZE, total)
            real_collection.upsert(
                ids        = all_data["ids"][start:end],
                documents  = all_data["documents"][start:end],
                embeddings = all_data["embeddings"][start:end],
                metadatas  = all_data["metadatas"][start:end],
            )
            gc.collect()    # ← free memory after every batch

        # ── Step 5: Clean up temp ──────────────────────────────────────
        local_client.delete_collection(COLLECTION_NAME_TEMP)
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
        try:
            if local_client:
                local_client.delete_collection(COLLECTION_NAME_TEMP)
                log_lines.append("Temp collection cleaned up after failure")
        except Exception:
            pass
        return {
            "success": False,
            "error":   str(e),
            "log":     log_lines,
        }

    finally:
        # ── Always unload model and client from RAM ────────────────────
        if local_model is not None:
            del local_model
            log_lines.append("Model unloaded from RAM.")
        if local_client is not None:
            del local_client
        gc.collect()