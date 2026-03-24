from typing import Optional
from pydantic import BaseModel

class QueryFeedback_pd(BaseModel):
    query: str
    llmresponse: str
    reason: str
    detail: str