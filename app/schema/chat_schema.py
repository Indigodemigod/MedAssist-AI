from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChatRequest(BaseModel):
    prescription_id: int
    session_id: Optional[int] = None
    question: str


class ChatResponse(BaseModel):
    session_id: int
    answer: str
    created_at: datetime
