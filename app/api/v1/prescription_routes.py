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

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])

UPLOAD_DIR = "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


@router.post("/", response_model=PrescriptionResponse)
def upload_prescription(
    user_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # 1️⃣ Save file
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())

        # 2️⃣ OCR
        # Validate file
        content_type = FileIngestionService.validate_file(file)

        # Save file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())

        # Extract text
        extracted_text = FileIngestionService.extract_text(file_path, content_type)

        if not extracted_text or extracted_text.strip() == "":
            raise HTTPException(
                status_code=400,
                detail="Unable to extract sufficient text from file."
            )

        if not extracted_text or extracted_text.strip() == "":
            raise HTTPException(status_code=400, detail="Unable to extract text from image.")

        # 3️⃣ Medicine extraction
        enriched_medicines = extract_and_enrich_medicines(extracted_text)

        # 5️⃣ Save to DB
        prescription = PrescriptionRepository.create_prescription(
            db=db,
            user_id=user_id,
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
            logger.error("Embedding generation failed.")
            raise HTTPException(status_code=500, detail="Embedding service failed.")

        for emb, chunk in zip(chunk_embeddings, chunks):
            store.add_chunk(emb, chunk)

        logger.info(f"RAG index built for Prescription ID: {prescription.id}")
        logger.info(f"Total OCR chunks indexed: {len(chunks)}")
        logger.info(f"Total structured medicines stored: {len(enriched_medicines)}")

        return prescription

    except Exception as e:
        logger.error(f"Prescription upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Prescription processing failed.")
