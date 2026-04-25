from pydantic import BaseModel


class GenerateRequest(BaseModel):
    semester: str

class EmbedRequest(BaseModel):
    semester: str
    wipe: bool = True

class SearchRequest(BaseModel):
    query: str
    top_k: int = 3