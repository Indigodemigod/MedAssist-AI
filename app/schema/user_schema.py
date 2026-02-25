from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    email: str
    full_name: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True

class UserSummaryResponse(BaseModel):
    full_name: str
    total_prescriptions: int
    total_medicines: int
    total_questions: int
    last_prescription_upload_time: Optional[datetime] = None
    last_prescription_name: Optional[str] = None

    class Config:
        from_attributes = True
