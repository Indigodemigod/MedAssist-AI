from app.services.vector_store_service import VectorStoreService
import logging
logger = logging.getLogger(__name__)

class VectorRegistry:
    """
    Holds vector stores per prescription in memory.
    """

    def __init__(self):
        self.registry = {}

    def create_store(self, prescription_id: int):
        logger.info(f"Creating FAISS store for prescription_id={prescription_id}")
        store = VectorStoreService()
        self.registry[prescription_id] = store
        return store

    def get_store(self, prescription_id: int):
        logger.info(f"Fetching FAISS store for prescription_id={prescription_id}")
        return self.registry.get(prescription_id)


vector_registry = VectorRegistry()
