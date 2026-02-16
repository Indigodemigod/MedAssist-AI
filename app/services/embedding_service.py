from google import genai
import os
import numpy as np
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_embeddings_batch(texts: list[str]):
    """
    Generate normalized embeddings for multiple texts in one API call.
    """

    response = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=texts
    )

    embeddings = []

    for emb in response.embeddings:
        vector = np.array(emb.values).astype("float32")

        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        embeddings.append(vector)

    return embeddings


def generate_embedding(text: str):
    """
    Generate normalized embedding using Gemini.
    """

    logger.info("Generating embedding from Gemini")

    response = client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text
    )

    vector = response.embeddings[0].values
    vector = np.array(vector).astype("float32")

    # Normalize for cosine similarity
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm

    logger.info(f"Embedding generated. Dimension: {len(vector)}")

    return vector
