from pydantic import BaseModel
from datetime import datetime

class SaveChatRequest(BaseModel):
    query:    str
    response: str

class SavedChatResponse(BaseModel):
    id:       int
    query:    str
    response: str
    saved_at: datetime

    class Config:
        from_attributes = True