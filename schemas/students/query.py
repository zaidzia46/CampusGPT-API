from typing import Optional
from pydantic import BaseModel

class Query(BaseModel):
    query_text: str