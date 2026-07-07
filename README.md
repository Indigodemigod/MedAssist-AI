# 🩺 MedAssist AI — AI-Powered Medical Prescription Assistant

MedAssist AI is a production-ready, Generative AI-powered healthcare backend that transforms raw or scanned prescription documents into interactive, context-aware digital assistants. The system uses Optical Character Recognition (OCR) to extract unstructured text from prescription uploads, parses and enriches it with medical data using the Gemini LLM, stores semantic context in an in-memory FAISS vector database, and serves structured answers to user prompts with strict medical guardrails.

---

## 🏗️ System Architecture

```
                               +-----------------------------+
                               |     User Interface (Web)    |
                               +--------------+--------------+
                                              |
                       Upload Document        |       Interactive Query
                      (PDF / JPG / PNG)       |       (Chat Assistant)
                               v              v
                       +----------------------+--------------+
                       |           FastAPI Backend           |
                       +-------+--------------------+--------+
                               |                    |
                               | (Ingestion / OCR)  | (Similarity Search)
                               v                    v
                       +-------+--------+   +-------+-------+
                       | pdfplumber /   |   |   In-Memory   |
                       | PyMuPDF /      |   |  FAISS Index  |
                       | EasyOCR        |   | (per prescr.) |
                       +-------+--------+   +-------+-------+
                               |                    ^
              Extracted Text   |                    |
              (Raw OCR Text)   |                    | Generates Embeddings
                               v                    | (gemini-embedding-001)
                       +-------+--------+           |
                       | Google Gemini  +-----------+
                       |  2.5  Flash    |
                       +-------+--------+
                               |
            Structured Payload | (Enrichment & Rules Engine)
                               v
                       +-------+--------+
                       | SQLite DB      |
                       | (medassist.db) |
                       +----------------+
```

---

## ⚡ Tech Stack

* **Backend Framework:** FastAPI (Uvicorn / Python 3.10+)
* **Database & Persistence:** SQLite with SQLAlchemy ORM
* **OCR Engines:** EasyOCR (Fallback/Images), pdfplumber (Direct PDF text), PyMuPDF (PDF render-to-image pipeline)
* **AI & LLM Services:** 
  * `gemini-2.5-flash` (Structured data extraction, medical enrichment, and conversational engine)
  * `models/gemini-embedding-001` (3072-dimension normalized embeddings)
* **Vector DB:** In-Memory FAISS (`IndexFlatIP` optimized for Cosine Similarity search)
* **Security & Auth:** PyJWT, bcrypt, Passlib (Secured Bearer Authentication)

---

## 🔧 Backend Modules & API Reference

### 🔐 User & Authentication Module

Handles registration, user authorization, and JWT authentication flows.

* **Register a New Account**
  * `POST /auth/register`
  * **Request Body (`RegisterRequest`):**
    ```json
    {
      "email": "user@example.com",
      "full_name": "John Doe",
      "password": "strongpassword123"
    }
    ```
  * **Response (`TokenResponse`):**
    ```json
    {
      "access_token": "ey...",
      "token_type": "bearer"
    }
    ```

* **LogIn User**
  * `POST /auth/login`
  * **Request Body (`LoginRequest`):**
    ```json
    {
      "email": "user@example.com",
      "password": "strongpassword123"
    }
    ```
  * **Response (`TokenResponse`):**
    ```json
    {
      "access_token": "ey...",
      "token_type": "bearer"
    }
    ```

* **Create User**
  * `POST /users/`
  * **Request Body (`UserCreate`):**
    ```json
    {
      "email": "user@example.com",
      "full_name": "John Doe"
    }
    ```
  * **Response (`UserResponse`):**
    ```json
    {
      "id": 1,
      "email": "user@example.com",
      "full_name": "John Doe",
      "created_at": "2026-07-07T12:00:00Z"
    }
    ```

* **Retrieve User Summary**
  * `GET /users/summary` (Requires Authentication Header)
  * **Headers:** `Authorization: Bearer <JWT_TOKEN>`
  * **Response (`UserSummaryResponse`):**
    ```json
    {
      "full_name": "John Doe",
      "total_prescriptions": 4,
      "total_medicines": 12,
      "total_questions": 35,
      "last_prescription_upload_time": "2026-07-07T12:30:00Z",
      "last_prescription_name": "prescription_july.png"
    }
    ```

---

### 📄 Prescriptions Module

Responsible for uploading files, performing OCR, parsing medication routines via AI, and auto-indexing the text inside the vector store.

* **Upload Prescription**
  * `POST /prescriptions/` (Requires Authentication Header)
  * **Request Multi-Part Data:**
    * `file`: UploadFile (Supports PNG, JPG, JPEG, PDF)
  * **Workflow:**
    1. **File Validation:** Restricts size to 10MB and validates file content type.
    2. **Storage:** Saves the uploaded artifact to the local `uploads/` directory.
    3. **OCR Extraction:** If image, processes using EasyOCR. If PDF, attempts direct text extraction using pdfplumber, falling back to rendering pages with PyMuPDF and running EasyOCR.
    4. **AI Parsing:** Calls Gemini `gemini-2.5-flash` to structure and enrich the medicines metadata.
    5. **Database Storage:** Saves results to SQL database (includes image path, extracted text, and the JSON structured analysis).
    6. **Vector Search Indexing:** Chunks the extracted text, creates embeddings using `gemini-embedding-001`, and initializes an in-memory FAISS vector index representing this specific prescription ID.
  * **Response (`PrescriptionResponse`):**
    ```json
    {
      "id": 1,
      "user_id": 1,
      "image_path": "uploads/prescription_july.png",
      "extracted_text": "Rx: Amoxicillin 500mg - 3 times a day for 5 days...",
      "analysis_result": [
        {
          "medicine_name": "Amoxicillin",
          "dosage": "500mg",
          "frequency": "3 times a day",
          "duration": "5 days",
          "administration_instructions": {
            "timing": "morning, afternoon, night",
            "food_relation": "after food",
            "special_notes": "Take with plenty of water"
          },
          "purpose": "Antibiotic to treat bacterial infections",
          "common_side_effects": "Diarrhea, nausea, skin rash",
          "warnings": "Finish the complete course even if symptoms disappear"
        }
      ],
      "created_at": "2026-07-07T12:30:00Z",
      "session_id": null
    }
    ```

* **List All Prescriptions**
  * `GET /prescriptions/` (Requires Authentication Header)
  * **Response:** Array of `PrescriptionResponse` containing all history uploaded by the current user.

* **Get Specific Prescription Detail**
  * `GET /prescriptions/{prescription_id}` (Requires Authentication Header)
  * **Response:** Singular `PrescriptionResponse` detail.

* **Update Code/Analysis Manually**
  * `PATCH /prescriptions/{prescription_id}/analysis`
  * **Request Body (`PrescriptionUpdate`):**
    ```json
    {
      "analysis_result": [
        {
          "medicine_name": "Amoxicillin",
          "dosage": "500mg",
          "frequency": "3 times a day",
          "duration": "7 days",
          "purpose": "Refined diagnostic purpose"
        }
      ]
    }
    ```
  * **Response:** Updated `PrescriptionResponse`.

---

### 💬 AI Medical Chat Module

Allows structured and semantic similarity searches over a patient's prescription documents.

* **Send Chat Query (Prescription Context Bound)**
  * `POST /chat/` or `POST /prescriptions/{prescription_id}/chat`
  * **Request Body (`ChatRequest`):**
    ```json
    {
      "prescription_id": 1,
      "session_id": null,
      "question": "How often should I take the Amoxicillin?"
    }
    ```
  * **Response (`ChatResponse`):**
    ```json
    {
      "session_id": 102,
      "answer": "You should take Amoxicillin 500mg 3 times a day (morning, afternoon, night) after food for a duration of 5 days.",
      "created_at": "2026-07-07T12:32:00Z"
    }
    ```
  * **Conversational Logic Router:**
    1. **General Query (ALL medicines):** If the user asks general questions ("What are all the medicines in my prescription?"), it is routed to explanations based on the structured JSON records.
    2. **Specific Medicine Matcher:** Matches medicine names to structured entities. Uses licensing instructions and structured parameters for high precision.
    3. **Semantic RAG (Fallback):** Generates query embeddings with `gemini-embedding-001`, queries the prescription's in-memory FAISS flat vector index, fetches top 8 chunks, and formats them into a bounded LLM context.

* **Fetch Session Message History**
  * `GET /chat/sessions/{session_id}/messages`
  * **Response:** List of `ChatMessageResponse` containing conversational turns (users and assistant).

* **Fetch Latest Prescription Conversation**
  * `GET /chat/prescription/{prescription_id}/conversations`
  * **Response:** Thread history of the latest active chat session associated with the prescription.

---

## 🛠️ Installation & Windows Setup Guide

Since you are running on Windows, follow these detailed steps to set up the environments and local database.

### 📋 Prerequisites
* Install [Python 3.10 or higher](https://www.python.org/downloads/) (Make sure **"Add Python to PATH"** is ticked during installation).
* Install [Git for Windows](https://gitforwindows.org/).

### ⚡ Installation Steps

1. **Clone the Repository:**
   ```bash
   git clone <repository-url>
   cd MedAssist-AI
   ```

2. **Create and Activate a Virtual Environment:**
   ```powershell
   # In PowerShell / Command Prompt:
   python -m venv paivenv
   
   # Activate on Windows (PowerShell):
   .\paivenv\Scripts\Activate.ps1
   
   # Activate on Windows (Command Prompt):
   .\paivenv\Scripts\activate.bat
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   > **Note on EasyOCR:** EasyOCR will download its language models (English) on the first run, which may take a few moments depending on network speeds.

4. **Environment Configuration:**
   Create a `.env` file in the root directory:
   ```env
   DATABASE_URL=sqlite:///./medassist.db
   GEMINI_API_KEY=your_google_gemini_api_key_here
   SECRET_KEY=generate_a_secure_jwt_secret_key_here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

5. **Start the FastAPI Server:**
   ```bash
   uvicorn app.main:app --reload
   ```
   The interactive Swagger documentation will be available at `http://127.0.0.1:8000/docs`.

---

## 🧠 System Assumptions

* **In-Memory Volatile FAISS Index:** FAISS vector stores are registered per-prescription ID **in memory** inside `VectorRegistry`. This assumes the server runs continuously. When the FastAPI process restarts, the FAISS indexes are flushed. (They are re-created when files get uploaded, or need rebuild functionality in subsequent server runs).
* **SQLite Single-Process Concurrency:** SQLite is configured locally (`medassist.db`). It operates under standard locking constraints. This database setup assumes lightweight, personal utilization and is not optimized for high-concurrent write operations.
* **OCR Reliability and Input Resolution:** EasyOCR assumes documents have clear text alignment, legible writing, and sufficient rendering contrast. Hand-written prescription performance is secondary to digitally printed (typewritten) sheets.
* **Gemini Availability:** Prescriptions processing and user chat queries assume a strong, low-latency internet connection to interface with the Google Gemini API.

---

## ⚠️ Technical & Operational Challenges

* **Scanned/Image PDF Handling:** Standard PDF parsers extract raw text streams, failing on scanned PDFs which output empty strings. **Solution:** The pipeline first tries direct text reading via `pdfplumber`. If the string return is empty or whitespace-only, it converts PDF pages to temporary PNG images via `PyMuPDF (fitz)` and uses `EasyOCR` to capture the medical text.
* **Structured Data Extraction Failures:** If the Gemini model returns a poorly formed JSON array (due to parser formatting issues), `extract_and_enrich_medicines` collapses. **Solution:** The app implements a structured regex cleaning method (`clean_json_response`) to remove markdown blocks and fallbacks to a simpler python regex medicine matching algorithm if the primary Gemini model fails.
* **Hallucination Mitigation:** Bounding an LLM to answer only from prescription details is fragile. **Solution:** Implemented **strict systemic prompts** in `prompt_builder.py` instructing Gemini to restrict responses solely to the structured medicine JSON payload and the raw OCR text. If queries involve external personal details or are out-of-scope (e.g. alcohol, contraband materials), prompt guardrails force a polite refusal.
* **Cold Start OCR Model latency:** EasyOCR loads the model weights into memory upon the first invocation, introducing a delay on the very first upload API request.

---

## 🚀 Future Scopes

* **Persistent Vector Store (Chromadb / Pgvector):** Migrate from volatile, in-memory FAISS indices to a permanent vector database like PGVector (PostgreSQL) or ChromaDB to keep structured semantic indices across server Restarts.
* **Automated Medication Reminders:** Build a background cron worker (e.g., Celery or APScheduler) to schedule email/SMS notifications based on the extracted `dosage` and `frequency` variables.
* **Drug-to-Drug Interaction Alerts:** Integrate external OpenAPI databases (e.g., RxNorm, RxClass) to compare structured medicine items and warn users about lethal drug combinations.
* **Multi-Prescription History & Synthesis:** Enable cross-document semantic synthesis to analyze treatment progress across multiple historical uploads.
* **Voice-Based Medical Assistant:** Integrate Whisper/STT APIs to permit hands-free voice transcription for asking questions to the AI assistant.
