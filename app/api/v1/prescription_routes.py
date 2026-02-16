import os
from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.prescription_repository import PrescriptionRepository
from app.schema.prescription_schema import PrescriptionResponse
from app.services.ocr_service import extract_text_from_image
from app.services.llm_service import (
    extract_medicines_from_text,
    enrich_medicine_info
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
        extracted_text = extract_text_from_image(file_path)

        if not extracted_text or extracted_text.strip() == "":
            raise HTTPException(status_code=400, detail="Unable to extract text from image.")

        # 3️⃣ Medicine extraction
        medicines = extract_medicines_from_text(extracted_text)

        # 4️⃣ Enrichment
        enriched_medicines = []
        for med in medicines:
            details = enrich_medicine_info(med["medicine_name"])
            med.update(details)
            enriched_medicines.append(med)

        # 5️⃣ Save to DB FIRST (we need prescription ID)
        prescription = PrescriptionRepository.create_prescription(
            db=db,
            user_id=user_id,
            image_path=file_path,
            extracted_text=extracted_text,
            analysis_result=enriched_medicines
        )

        # 6️⃣ Build RAG Vector Index (per prescription)
        normalized_text = extracted_text.lower()
        chunks = chunk_text(normalized_text)

        store = vector_registry.create_store(prescription.id)

        chunk_embeddings = generate_embeddings_batch(chunks)

        for emb, chunk in zip(chunk_embeddings, chunks):
            store.add_chunk(emb, chunk)

        # 7️⃣ Add structured enriched medicines to vector store
        med_texts = []

        for med in enriched_medicines:
            med_text = f"""
            Medicine Name: {med.get('medicine_name', '')}
            Dosage: {med.get('dosage', '')}
            Frequency: {med.get('frequency', '')}
            Duration: {med.get('duration', '')}
            Purpose: {med.get('purpose', '')}
            """
            med_texts.append(med_text.lower())

        if med_texts:
            med_embeddings = generate_embeddings_batch(med_texts)

            for emb, text in zip(med_embeddings, med_texts):
                store.add_chunk(emb, text)


        logger.info(f"RAG index built for Prescription ID: {prescription.id}")
        logger.info(f"Total OCR chunks indexed: {len(chunks)}")
        logger.info(f"Total structured medicines indexed: {len(enriched_medicines)}")

        return prescription

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
