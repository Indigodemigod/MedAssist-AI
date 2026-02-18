import os
from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.prescription_repository import PrescriptionRepository
from app.schema.prescription_schema import PrescriptionResponse
from app.services.file_ingestion_service import FileIngestionService
from app.services.llm_service import (
    extract_medicines_from_text, extract_and_enrich_medicines
)
from app.utils.text_chunker import chunk_text
from app.services.embedding_service import generate_embedding, generate_embeddings_batch
from app.services.vector_registry import vector_registry
import logging
logger = logging.getLogger(__name__)
from typing import List
from app.schema.prescription_schema import PrescriptionUpdate
from app.schema.chat_schema import ChatRequest
from app.schema.chat_schema import ChatResponse
from app.repositories.chat_repository import ChatRepository
from app.models.prescription import Prescription
from fastapi import Path, Query
from app.services.chat_service import ChatService
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])

UPLOAD_DIR = "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


@router.post("/", response_model=PrescriptionResponse)
def upload_prescription(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        # 1️⃣ Validate file first (checks content_type and size)
        try:
            content_type = FileIngestionService.validate_file(file)
        except ValueError as ve:
            logger.warning(f"File validation failed: {ve}")
            raise HTTPException(status_code=400, detail=str(ve))

        # 2️⃣ Save file (single write). Use basename to avoid path traversal.
        filename = os.path.basename(file.filename)
        file_path = os.path.join(UPLOAD_DIR, filename)

        file.file.seek(0)
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())

        # 3️⃣ Extract text
        extracted_text = FileIngestionService.extract_text(file_path, content_type)

        if not extracted_text or extracted_text.strip() == "":
            raise HTTPException(
                status_code=400,
                detail="Unable to extract sufficient text from file."
            )

        # 4️⃣ Medicine extraction (LLM) with fallback
        enriched_medicines = extract_and_enrich_medicines(extracted_text)
        if not enriched_medicines:
            logger.warning("LLM extraction returned empty; falling back to simple extractor.")
            try:
                fallback = extract_medicines_from_text(extracted_text)
                if isinstance(fallback, list):
                    enriched_medicines = fallback
                else:
                    enriched_medicines = []
            except Exception as e:
                logger.error("Fallback extraction also failed: %s", e, exc_info=e)
                enriched_medicines = []

        # 5️⃣ Save to DB
        prescription = PrescriptionRepository.create_prescription(
            db=db,
            user_id=current_user.id,
            image_path=file_path,
            extracted_text=extracted_text,
            analysis_result=enriched_medicines
        )

        # 6️⃣ Build RAG Vector Index (OCR text only)
        normalized_text = extracted_text.lower()
        chunks = chunk_text(normalized_text)

        store = vector_registry.create_store(prescription.id)

        try:
            chunk_embeddings = generate_embeddings_batch(chunks)
        except Exception as e:
            logger.error("Embedding generation failed.", exc_info=e)
            raise HTTPException(status_code=500, detail="Embedding service failed.")

        for emb, chunk in zip(chunk_embeddings, chunks):
            store.add_chunk(emb, chunk)

        logger.info(f"RAG index built for Prescription ID: {prescription.id}")
        logger.info(f"Total OCR chunks indexed: {len(chunks)}")
        logger.info(f"Total structured medicines stored: {len(enriched_medicines)}")

        return prescription

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prescription upload failed: {str(e)}", exc_info=e)
        raise HTTPException(status_code=500, detail="Prescription processing failed.")


@router.get("/", response_model=List[PrescriptionResponse])
def list_prescriptions(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return PrescriptionRepository.get_prescriptions_by_user(db, current_user.id)


@router.get("/{prescription_id}", response_model=PrescriptionResponse)
def get_prescription(prescription_id: int = Path(...), db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    pres = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not pres:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return pres


@router.patch("/{prescription_id}/analysis", response_model=PrescriptionResponse)
def patch_prescription_analysis(prescription_id: int, update: PrescriptionUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    pres = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not pres:
        raise HTTPException(status_code=404, detail="Prescription not found")
    pres.analysis_result = update.analysis_result
    db.add(pres)
    db.commit()
    db.refresh(pres)
    return pres


@router.post("/{prescription_id}/chat", response_model=ChatResponse)
def prescription_chat(prescription_id: int, request: ChatRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Ensure prescription exists
    pres = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not pres:
        raise HTTPException(status_code=404, detail="Prescription not found")

    session_id, answer, created_at = ChatService.handle_chat(
        db=db,
        prescription_id=prescription_id,
        session_id=request.session_id,
        question=request.question
    )

    return ChatResponse(session_id=session_id, answer=answer, created_at=created_at)