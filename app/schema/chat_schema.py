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


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
