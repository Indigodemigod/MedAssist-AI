from fastapi import FastAPI
from app.core.database import engine
from app.models import user, prescription
from app.core.database import Base
from app.api.v1 import prescription_routes
from app.api.v1 import user_routes

app = FastAPI(title="MedAssist AI")

Base.metadata.create_all(bind=engine)

app.include_router(user_routes.router)
app.include_router(prescription_routes.router)



@app.get("/")
def root():
    return {"message": "MedAssist AI running with DB"}
