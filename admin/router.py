import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from admin.deps import get_current_admin
from db.session import get_db
from core.security import create_access_token, create_access_token, create_refresh_token, verify_password
from models.models import UserAuth
from rag_pipeline.generator import generate
from rag_pipeline.embedder  import embed
from rag_pipeline.searcher  import search
from schemas.admin.admin import EmbedRequest, GenerateRequest, SearchRequest


public_router = APIRouter(prefix='/admin', tags=['Admin'])

protected_router = APIRouter(
    prefix='/admin',
    tags=['Admin'],
    dependencies=[Depends(get_current_admin)]
)

ROOT       = Path(__file__).parent.parent
CHUNKS_DIR = ROOT / "UNIdata" / "chunks"

@public_router.post('/login')
def admin_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserAuth).filter(UserAuth.email == form_data.username).first()

    if user is None or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=403, detail='Wrong email or password')

    if user.role != 'admin':
        raise HTTPException(status_code=403, detail='You are not authorized as admin')

    access_token  = create_access_token({'sub': str(user.id), 'role': user.role})
    refresh_token = create_refresh_token({'sub': str(user.id), 'role': user.role})

    return {
        'access_token':  access_token,
        'refresh_token': refresh_token,
        'token_type':    'bearer'
    }

@protected_router.get('/status')
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


@protected_router.post('/generate')
def admin_generate(req: GenerateRequest):
    """Generate chunks from Google Sheets for the given semester."""
    result = generate(req.semester)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result)
    return result


@protected_router.post('/embed')
def admin_embed(req: EmbedRequest):
    """Embed chunks into ChromaDB."""
    result = embed(req.semester, req.wipe)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result)
    return result


@protected_router.get('/chunks')
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


@protected_router.post('/search')
def admin_search(req: SearchRequest):
    """Test search against ChromaDB — for admin quality checking."""
    result = search(req.query, req.top_k)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result