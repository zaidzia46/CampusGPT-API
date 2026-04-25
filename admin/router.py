import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from admin.deps import get_current_admin
from rag_pipeline.generator import generate
from rag_pipeline.embedder  import embed
from rag_pipeline.searcher  import search
from schemas.admin.admin import EmbedRequest, GenerateRequest, SearchRequest

router = APIRouter(
    prefix='/admin',
    tags=['Admin'],
    dependencies=[Depends(get_current_admin)]
)

ROOT       = Path(__file__).parent.parent
CHUNKS_DIR = ROOT / "UNIdata" / "chunks"

@router.get('/status')
def status():
    """Returns list of all generated chunk files."""
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


@router.post('/generate')
def admin_generate(req: GenerateRequest):
    """Generate chunks from Google Sheets for the given semester."""
    result = generate(req.semester)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result)
    return result


@router.post('/embed')
def admin_embed(req: EmbedRequest):
    """Embed chunks into ChromaDB."""
    result = embed(req.semester, req.wipe)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result)
    return result


@router.get('/chunks')
def admin_chunks(semester: str):
    """Returns the chunks JSON for a given semester."""
    chunk_file = CHUNKS_DIR / f"chunks_{semester}.json"
    if not chunk_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No chunk file found for semester '{semester}'."
        )
    with open(chunk_file, encoding="utf-8") as f:
        return json.load(f)


@router.post('/search')
def admin_search(req: SearchRequest):
    """Test search against ChromaDB — for admin quality checking."""
    result = search(req.query, req.top_k)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result