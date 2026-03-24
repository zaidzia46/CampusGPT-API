from typing import Optional
from pydantic import BaseModel

class Feedback_pd(BaseModel):
    feedback: str
    rating: Optional[int] = None