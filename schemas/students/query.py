from typing import Optional
from pydantic import BaseModel, Field

class Query(BaseModel):
    query_text: str = Field(..., min_length=1, max_length=500)