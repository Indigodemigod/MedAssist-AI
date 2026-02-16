import json
import re
from google import genai
from app.core.config import settings
import logging
import time

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.GEMINI_API_KEY)


def clean_json_response(text: str):
    # Remove markdown if present
    text = re.sub(r"```json|```", "", text)
    text = text.strip()
    return text


def enrich_medicine_info(medicine_name: str):
    prompt = f"""
    Provide medical information about {medicine_name}.

    Return ONLY JSON in this format:

    {{
      "purpose": "",
      "common_side_effects": "",
      "warnings": ""
    }}

    No markdown.
    No explanation.
    """

    try:
        start = time.time()
        logger.info("Calling Gemini model for extraction")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        logger.info(f"Gemini response received in {time.time() - start:.2f}s")
        cleaned = clean_json_response(response.text)
        parsed = json.loads(cleaned)
        return parsed

    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        return {"error": str(e)}


def extract_medicines_from_text(ocr_text: str):
    prompt = f"""
    You are a medical prescription analyzer.

    Extract structured medicine information from the following text.

    Return ONLY valid JSON array.
    Do NOT include markdown.
    Do NOT include explanations.
    
    Find the purpose of the medicine, if it is not in you knowledge just return the issue the medicine resolves
    
    Format:

    [
      {{
        "medicine_name": "",
        "dosage": "",
        "frequency": "",
        "duration": "",
        "purpose": ""
      }}
    ]

    Prescription Text:
    {ocr_text}
    """

    try:
        start = time.time()
        logger.info("Calling Gemini model for extraction")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        logger.info(f"Gemini response received in {time.time() - start:.2f}s")
        cleaned = clean_json_response(response.text)

        parsed = json.loads(cleaned)

        if not isinstance(parsed, list):
            raise ValueError("LLM did not return list")

        return parsed
    except Exception as e:
        logger.error(f"LLM was not able to generate response: {e}")
        return f"LLM Error: {str(e)}"
