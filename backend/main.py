from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config.settings import settings
from backend.database import init_db, SessionLocal
from backend.services.synthetic_data import seed_synthetic_patients
from backend.models.patient import Patient
from backend.api.v1.router import api_v1_router
from backend.schemas.common import DecisionSupportBanner

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB and seed synthetic personas if empty
    init_db()
    db = SessionLocal()
    try:
        count = db.query(Patient).count()
        if count == 0:
            seed_synthetic_patients(db, force_recreate=False)
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Clinical Decision Support Prototype for Longitudinal PCOS Patient Tracking",
    lifespan=lifespan
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes under root, /api, and /api/v1 for comprehensive spec and frontend compatibility
app.include_router(api_v1_router)
app.include_router(api_v1_router, prefix="/api")
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "decision_support": DecisionSupportBanner(),
        "docs_url": "/docs",
        "api_v1": "/api/v1"
    }

@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "pcos-longitudinal-tracker-backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
