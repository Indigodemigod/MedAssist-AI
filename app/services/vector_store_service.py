import faiss
import numpy as np
import logging
logger = logging.getLogger(__name__)


class VectorStoreService:
    """
    In-memory FAISS store per prescription.
    """

    def __init__(self, dimension: int = 3072):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.chunks = []

    def add_chunk(self, embedding: np.ndarray, text_chunk: str):
        embedding = np.expand_dims(embedding, axis=0)
        self.index.add(embedding)
        self.chunks.append(text_chunk)
        logger.info(f"Chunk added to FAISS. Total chunks: {len(self.chunks)}")

    def search(self, query_embedding: np.ndarray, top_k: int = 3):
        query_embedding = np.expand_dims(query_embedding, axis=0)
        distances, indices = self.index.search(query_embedding, top_k)
        logger.info(f"FAISS search performed. Top K: {top_k}")
        results = []
        for idx in indices[0]:
            if idx < len(self.chunks):
                results.append(self.chunks[idx])
        logger.info(f"Retrieved {len(results)} relevant chunks")
        return results
