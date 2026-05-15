from pydantic import BaseModel


class GenerateRequest(BaseModel):
    semester: str

class EmbedRequest(BaseModel):
    semester: str
    wipe: bool = True

class SearchRequest(BaseModel):
    query: str
    top_k: int = 3

class AnnouncementBody(BaseModel):
    title:           str
    description:     str
    type:            str = "General"
    target_audience: str = ""        # free text now
    is_active:       str = "Yes"
    semester:        str
