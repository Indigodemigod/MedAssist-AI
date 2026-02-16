from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schema.chat_schema import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    session_id, answer, created_at = ChatService.handle_chat(
        db=db,
        prescription_id=request.prescription_id,
        session_id=request.session_id,
        question=request.question
    )

    return ChatResponse(
        session_id=session_id,
        answer=answer,
        created_at=created_at
    )
