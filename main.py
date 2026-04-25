from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from auth.router import router as auth_router
from students.router import router as students_router
from admin.router import router as admin_router
from models import models
from db.session import engine
from core.security import router as refresh_router
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="CmapusGPT API", description="API for CampusGPT application", version="1.0.0")
app.mount('/static-pwd-reset', StaticFiles(directory='static-pwd-reset'), name='static-pwd-reset')

app.include_router(auth_router)
app.include_router(students_router)
app.include_router(admin_router)
app.include_router(refresh_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def getme():
    return{'message': 'API connects'}

models.base.metadata.create_all(bind=engine)