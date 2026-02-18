from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any
class PrescriptionResponse(BaseModel):
    id: int
    user_id: int
    image_path: str
    extracted_text: str
    analysis_result: List[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class PrescriptionUpdate(BaseModel):
    analysis_result: List[Dict[str, Any]]

    class Config:
        schema_extra = {"example": {"analysis_result": []}}
