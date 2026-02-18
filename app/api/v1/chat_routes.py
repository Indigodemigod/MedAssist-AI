from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schema.chat_schema import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.repositories.chat_repository import ChatRepository
from app.schema.chat_schema import ChatMessageResponse
from typing import List
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
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


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
def get_session_messages(session_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    messages = ChatRepository.get_last_messages(db, session_id, limit=100)
    return [
        ChatMessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            created_at=m.created_at
        )
        for m in messages
    ]
