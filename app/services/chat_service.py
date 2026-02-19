from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.prescription import Prescription
from app.repositories.chat_repository import ChatRepository
from app.services.llm_service import client
from app.utils.medicine_matcher import MedicineMatcher
from app.services.prompt_builder import (
    build_structured_prompt,
    build_rag_prompt
)
from app.services.embedding_service import generate_embedding
from app.services.vector_registry import vector_registry
import logging
import json

logger = logging.getLogger(__name__)


class ChatService:

    @staticmethod
    def handle_chat(db: Session, prescription_id: int, session_id: int, question: str):

        logger.info(f"Processing chat for prescription_id={prescription_id}")

        # Normalize question
        question = question.strip()
        question_lower = question.lower()

        # 1️⃣ Validate prescription
        prescription = db.query(Prescription).filter(
            Prescription.id == prescription_id
        ).first()

        if not prescription:
            logger.warning("Prescription not found")
            raise HTTPException(status_code=404, detail="Prescription not found")

        # 2️⃣ Session handling
        if session_id:
            session = ChatRepository.get_session(db, session_id, prescription_id)
            if not session:
                raise HTTPException(status_code=404, detail="Invalid session")
        else:
            session = ChatRepository.create_session(db, prescription_id)

        logger.info(f"Chat session ID: {session.id}")

        # 3️⃣ Save user message
        ChatRepository.save_message(db, session.id, "user", question)

        # 4️⃣ Fetch recent history (exclude current message for clean context)
        history = ChatRepository.get_last_messages(db, session.id, limit=10)

        conversation = ""
        for msg in history[:-1]:
            conversation += f"{msg.role}: {msg.content}\n"

        # 5️⃣ Parse structured analysis safely
        analysis_result = prescription.analysis_result or []

        if isinstance(analysis_result, str):
            try:
                analysis_result = json.loads(analysis_result)
            except Exception:
                logger.warning("Failed to parse analysis_result JSON.")
                analysis_result = []

        if not isinstance(analysis_result, list):
            analysis_result = []

        # 6️⃣ Detect General Structured Intent (ALL medicines)
        general_keywords = [
            "each", "all", "everything",
            "complete", "full", "entire",
            "medicines", "drugs", "prescribed"
        ]

        is_general_query = any(word in question_lower for word in general_keywords)

        # 7️⃣ Detect Structured Medicine Match
        match_result = MedicineMatcher.detect(question, analysis_result)

        # 🔵 ROUTE 1: GENERAL STRUCTURED
        if is_general_query:
            logger.info("General structured query detected. Returning ALL medicines.")

            prompt = build_structured_prompt(
                question=question,
                medicines=analysis_result,
                history=conversation,
                raw_text=prescription.extracted_text
            )

        # 🔵 ROUTE 2: SPECIFIC MEDICINE STRUCTURED
        elif match_result["type"]:
            logger.info(
                f"Specific structured route triggered. Type: {match_result['type']}"
            )

            prompt = build_structured_prompt(
                question=question,
                medicines=match_result["medicines"],
                history=conversation,
                raw_text=prescription.extracted_text
            )

        # 🔵 ROUTE 3: RAG (Fallback)
        else:
            logger.info("RAG route triggered.")

            store = vector_registry.get_store(prescription_id)

            if not store:
                logger.warning(
                    "Vector store not found. Falling back to full prescription text."
                )
                retrieved_chunks = [prescription.extracted_text]

            else:
                logger.info("Vector store found. Performing semantic retrieval.")
                try:
                    question_embedding = generate_embedding(question_lower)
                    retrieved_chunks = store.search(question_embedding, top_k=8)
                    logger.info(f"Retrieved {len(retrieved_chunks)} chunks from vector store.")
                except Exception as e:
                    logger.error(f"Embedding/RAG error: {str(e)}")
                    retrieved_chunks = [prescription.extracted_text]

            prompt = build_rag_prompt(
                question=question,
                retrieved_chunks=retrieved_chunks,
                history=conversation
            )

        # 8️⃣ Generate Response
        logger.info("Generating response from Gemini")

        try:
            response = client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=prompt
            )
        except Exception as e:
            logger.error(f"LLM error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="AI service temporarily unavailable. Please try again."
            )

        answer = response.text.strip()

        # 9️⃣ Save assistant message
        assistant_msg = ChatRepository.save_message(
            db, session.id, "assistant", answer
        )

        logger.info("Chat response generated successfully")

        return session.id, answer, assistant_msg.created_at
