import datetime
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from admin.deps import get_current_admin
from core.notifications import notify_all_users
from db.session import get_db
from core.security import create_access_token, create_access_token, create_refresh_token, verify_password
from models.models import FacultySubmission, UserAuth, Announcement
from rag_pipeline.generator import generate
from rag_pipeline.embedder  import embed
from rag_pipeline.searcher  import search
from rag_pipeline.sheets_reader import append_to_faculty_sheet
from schemas.admin.admin import AnnouncementBody, EmbedRequest, GenerateRequest, SearchRequest


import shutil
import zipfile
from fastapi import UploadFile, File


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

@protected_router.get('/announcements')
def get_announcements(
    semester: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Announcement)
    if semester:
        query = query.filter(Announcement.semester == semester)
    items = query.order_by(Announcement.created_at.desc()).all()
    return [
        {
            "id":              a.id,
            "title":           a.title,
            "description":     a.description,
            "type":            a.type,
            "target_audience": a.target_audience,
            "is_active":       a.is_active,
            "semester":        a.semester,
            "created_at":      a.created_at.isoformat(),
        }
        for a in items
    ]
 
 
# POST /admin/announcements — create new
@protected_router.post('/announcements')
def create_announcement(body: AnnouncementBody, db: Session = Depends(get_db)):
    if not body.semester.strip() or not body.title.strip() or not body.description.strip():
        raise HTTPException(status_code=422, detail="Some fields are empty.")
    ann = Announcement(
        title           = body.title.strip(),
        description     = body.description.strip(),
        type            = body.type,
        target_audience = body.target_audience.strip(),
        is_active       = body.is_active,
        semester        = body.semester.strip(),
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)

    notifications_created = notify_all_users(db, ann.id)
    
    return {
        "id": ann.id,
        "message": "Announcement created successfully",
        "notifications_created": notifications_created,
    }
 
 
# PUT /admin/announcements/{id} — update existing
@protected_router.put('/announcements/{ann_id}')
def update_announcement(ann_id: int, body: AnnouncementBody, db: Session = Depends(get_db)):
    ann = db.query(Announcement).filter(Announcement.id == ann_id).first()
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")

    if not body.semester.strip() or not body.title.strip() or not body.description.strip():
        raise HTTPException(status_code=422, detail="Some fields are empty.")

    ann.title           = body.title.strip()
    ann.description     = body.description.strip()
    ann.type            = body.type
    ann.target_audience = body.target_audience.strip()
    ann.is_active       = body.is_active
    ann.semester        = body.semester.strip()

    db.commit()
    return {"message": "Announcement updated successfully"}
 
 
# PATCH /admin/announcements/{id}/toggle — toggle active/inactive
@protected_router.patch('/announcements/{ann_id}/toggle')
def toggle_announcement(ann_id: int, db: Session = Depends(get_db)):
    ann = db.query(Announcement).filter(Announcement.id == ann_id).first()
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")
 
    ann.is_active = "No" if ann.is_active == "Yes" else "Yes"
    db.commit()
    return {
        "id":        ann.id,
        "is_active": ann.is_active,
        "message":   f"Announcement {'activated' if ann.is_active == 'Yes' else 'deactivated'}",
    }
 
 
# DELETE /admin/announcements/{id} — delete
@protected_router.delete('/announcements/{ann_id}')
def delete_announcement(ann_id: int, db: Session = Depends(get_db)):
    ann = db.query(Announcement).filter(Announcement.id == ann_id).first()
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")
 
    db.delete(ann)
    db.commit()
    return {"message": "Announcement deleted successfully"}

# GET all submissions (filterable by status)
@protected_router.get("/submissions")
def get_submissions(
    status: str = None,
    db:     Session = Depends(get_db)
):
    query = db.query(FacultySubmission)
    if status:
        query = query.filter(FacultySubmission.status == status)
    items = query.order_by(FacultySubmission.submitted_at.desc()).all()
    return items


# PATCH approve — writes to Google Sheet on approval
@protected_router.patch("/submissions/{sub_id}/approve")
def approve_submission(
    sub_id:     int,
    admin_notes: str = "",
    db:          Session = Depends(get_db)
):
    sub = db.query(FacultySubmission).filter(
        FacultySubmission.id == sub_id
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    sub.status      = "Approved"
    sub.admin_notes = admin_notes
    sub.reviewed_at = datetime.datetime.utcnow()
    db.commit()

    # write clean row to Google Sheet
    append_to_faculty_sheet({
        "faculty_name": sub.faculty_name,
        "topic":        sub.topic,
        "detail":       sub.detail,
        "tags":         sub.tags or "",
        "file_url":     sub.file_url or "",
    })

    return {"message": "Approved and written to Google Sheet"}


# PATCH reject
@protected_router.patch("/submissions/{sub_id}/reject")
def reject_submission(
    sub_id:      int,
    admin_notes: str = "",
    db:          Session = Depends(get_db)
):
    sub = db.query(FacultySubmission).filter(
        FacultySubmission.id == sub_id
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    sub.status      = "Rejected"
    sub.admin_notes = admin_notes
    sub.reviewed_at = datetime.datetime.utcnow()
    db.commit()

    return {"message": "Submission rejected"}

@protected_router.post('/upload-vectordb')
async def upload_vectordb(file: UploadFile = File(...)):
    vectordb_path = ROOT / "UNIdata" / "vectordb"
    zip_path      = ROOT / "vectordb_upload.zip"

    # save uploaded zip
    with open(zip_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # DON'T delete the folder — just overwrite files inside it
    vectordb_path.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(str(vectordb_path))

    zip_path.unlink()

    return {"message": "VectorDB uploaded successfully"}