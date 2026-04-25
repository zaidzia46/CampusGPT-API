import json
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from admin.deps import get_current_admin
from schemas.admin.admin import EmbedRequest, GenerateRequest, SearchRequest

router = APIRouter(
    prefix='/admin',
    tags=['Admin'],
    dependencies=[Depends(get_current_admin)]
)

CHUNKS_DIR = Path("data/chunks")

@router.get("/status")
def status():
    files = []
    for f in sorted(CHUNKS_DIR.glob("chunks_*.json"), reverse=True):
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)
        files.append({
            "file":         f.name,
            "semester":     data.get("semester"),
            "total_chunks": data.get("total_chunks"),
            "generated_at": data.get("generated_at"),
        })
    return {"chunk_files": files}


@router.post("/generate")
def generate(req: GenerateRequest):
    result = subprocess.run(
        [sys.executable, "generate_chunks.py", "--semester", req.semester],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail={
            "message": "Chunk generation failed",
            "output":  result.stdout + result.stderr,
        })

    chunk_file = CHUNKS_DIR / f"chunks_{req.semester}.json"
    summary = {}
    if chunk_file.exists():
        with open(chunk_file, encoding="utf-8") as f:
            data = json.load(f)
        types = {}
        for c in data["chunks"]:
            t = c["chunk_type"]
            types[t] = types.get(t, 0) + 1
        summary = {
            "total_chunks": data["total_chunks"],
            "by_type":      types,
            "generated_at": data["generated_at"],
        }

    return {
        "success":  True,
        "semester": req.semester,
        "summary":  summary,
        "output":   result.stdout + result.stderr,
    }


@router.post("/embed")
def embed(req: EmbedRequest):
    chunk_file = CHUNKS_DIR / f"chunks_{req.semester}.json"

    if not chunk_file.exists():
        raise HTTPException(status_code=404, detail={
            "message": f"No chunk file for '{req.semester}'. Run /admin/generate first.",
        })

    args = [sys.executable, "embed_chunks.py", "--file", str(chunk_file)]
    if req.wipe:
        args.append("--wipe")

    result = subprocess.run(args, capture_output=True, text=True)

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail={
            "message": "Embedding failed",
            "output":  result.stdout + result.stderr,
        })

    return {
        "success":  True,
        "semester": req.semester,
        "wiped":    req.wipe,
        "output":   result.stdout + result.stderr,
    }


@router.get("/chunks")
def get_chunks(semester: str):
    chunk_file = CHUNKS_DIR / f"chunks_{semester}.json"

    if not chunk_file.exists():
        raise HTTPException(status_code=404, detail={
            "message": f"No chunk file found for semester '{semester}'.",
        })

    with open(chunk_file, encoding="utf-8") as f:
        data = json.load(f)
    return data


@router.post("/search")
def search(req: SearchRequest):
    try:
        import chromadb
        from chromadb.config import Settings
        from sentence_transformers import SentenceTransformer

        client = chromadb.PersistentClient(
            path=str(Path("data/vectordb").resolve()),
            settings=Settings(anonymized_telemetry=False),
        )
        collection = client.get_collection("cui_sahiwal_kb")
        model      = SentenceTransformer("all-MiniLM-L6-v2")

        vector  = model.encode(req.query).tolist()
        results = collection.query(
            query_embeddings=[vector],
            n_results=req.top_k,
        )

        hits = []
        for i in range(len(results["ids"][0])):
            hits.append({
                "chunk_id": results["ids"][0][i],
                "text":     results["documents"][0][i],
                "distance": round(results["distances"][0][i], 4),
                "metadata": results["metadatas"][0][i],
            })

        return {"query": req.query, "results": hits}

    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "message": f"Search failed: {str(e)}",
        })