from sqlalchemy.orm import Session
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
import logging

logger = logging.getLogger(__name__)


class ChatRepository:

    @staticmethod
    def create_session(db: Session, prescription_id: int):
        session = ChatSession(prescription_id=prescription_id)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_session(db: Session, session_id: int, prescription_id: int):
        return db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.prescription_id == prescription_id
        ).first()

    @staticmethod
    def save_message(db: Session, session_id: int, role: str, content: str):
        logger.info(f"Saving message for session {session_id}, role={role}")
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def get_last_messages(db: Session, session_id: int, limit: int = 10):
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.desc()).limit(limit).all()

        return list(reversed(messages))
