from fastapi import FastAPI, Request
from app.core.database import engine
from app.models import user, prescription
from app.core.database import Base
from app.api.v1 import prescription_routes
from app.api.v1 import user_routes
from app.api.v1 import chat_routes
from app.api.v1 import auth_routes
from app.core.logging_config import setup_logging
import logging
import time

setup_logging()
logger = logging.getLogger(__name__)


app = FastAPI(title="MedAssist AI")

Base.metadata.create_all(bind=engine)

app.include_router(user_routes.router)
app.include_router(prescription_routes.router)
app.include_router(chat_routes.router)
app.include_router(auth_routes.router)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    logger.info(f"Incoming request: {request.method} {request.url}")

    try:
        response = await call_next(request)
    except Exception as e:
        logger.exception(f"Unhandled error: {str(e)}")
        raise

    process_time = time.time() - start_time
    logger.info(
        f"Completed {request.method} {request.url} "
        f"Status: {response.status_code} "
        f"Time: {process_time:.3f}s"
    )

    return response


@app.get("/")
def root():
    return {"message": "MedAssist AI running with DB"}
