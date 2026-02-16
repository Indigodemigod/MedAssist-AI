from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.prescription import Prescription
from app.repositories.chat_repository import ChatRepository
from app.services.llm_service import client
from app.services.embedding_service import generate_embedding
from app.services.vector_registry import vector_registry
import logging

logger = logging.getLogger(__name__)


class ChatService:

    @staticmethod
    def handle_chat(db: Session, prescription_id: int, session_id: int, question: str):
        logger.info(f"Processing chat for prescription_id={prescription_id}")

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

        # 4️⃣ Fetch recent history
        history = ChatRepository.get_last_messages(db, session.id, limit=10)

        conversation = ""
        for msg in history:
            conversation += f"{msg.role}: {msg.content}\n"

        # 5️⃣ RAG Retrieval
        store = vector_registry.get_store(prescription_id)

        if store:
            logger.info("Vector store found. Performing semantic retrieval.")
            question_embedding = generate_embedding(question)
            relevant_chunks = store.search(question_embedding, top_k=5)
            retrieved_context = "\n".join(relevant_chunks)
            logger.info("Retrieved context for RAG:")
            logger.info(retrieved_context[:300])  # avoid logging full text
        else:
            logger.warning("Vector store not found. Falling back to full prescription text.")
            retrieved_context = prescription.extracted_text
            logger.info("Retrieved context for RAG:")
            logger.info(retrieved_context[:300])  # avoid logging full text

        # 6️⃣ Build grounded prompt
        prompt = f"""
                You are a medical assistant chatbot.
                
                STRICT RULES:
                - Use ONLY the retrieved context.
                - If answer not found in context, say: "The prescription does not mention this."
                - Do not hallucinate.
                - Be medically safe and conservative.
                
                Retrieved Context:
                {retrieved_context}
                
                Conversation History:
                {conversation}
                
                User Question:
                {question}
                """

        logger.info("Generating response from Gemini")

        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt
        )

        answer = response.text.strip()

        # 7️⃣ Save assistant message
        assistant_msg = ChatRepository.save_message(
            db, session.id, "assistant", answer
        )

        logger.info("Chat response generated successfully")

        return session.id, answer, assistant_msg.created_at
