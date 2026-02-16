from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.prescription import Prescription
from app.repositories.chat_repository import ChatRepository
from app.services.llm_service import client
import logging

logger = logging.getLogger(__name__)


class ChatService:

    @staticmethod
    def handle_chat(db: Session, prescription_id: int, session_id: int, question: str):
        logger.info(f"Processing chat for prescription_id={prescription_id}")

        prescription = db.query(Prescription).filter(
            Prescription.id == prescription_id
        ).first()

        if not prescription:
            logger.warning("Prescription not found")
            raise HTTPException(status_code=404, detail="Prescription not found")

        # Session handling
        if session_id:
            session = ChatRepository.get_session(db, session_id, prescription_id)
            if not session:
                raise HTTPException(status_code=404, detail="Invalid session")
        else:
            session = ChatRepository.create_session(db, prescription_id)

        logger.info(f"Chat session ID: {session.id}")

        # Save user message
        ChatRepository.save_message(db, session.id, "user", question)

        # Fetch history
        history = ChatRepository.get_last_messages(db, session.id)

        logger.info("Generating chat response from LLM")

        conversation = ""
        for msg in history:
            conversation += f"{msg.role}: {msg.content}\n"

        context = f"""
        Prescription Text:
        {prescription.extracted_text}

        Medicine Analysis:
        {prescription.analysis_result}
        """

        prompt = f"""
        You are a medical assistant chatbot.

        Use ONLY provided context.
        Do not hallucinate.

        Context:
        {context}

        Conversation:
        {conversation}
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        answer = response.text

        assistant_msg = ChatRepository.save_message(
            db, session.id, "assistant", answer
        )
        logger.info("Chat response generated successfully")
        return session.id, answer, assistant_msg.created_at
