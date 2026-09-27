from fastapi import APIRouter
from backend.api.auth import router as auth_router
from backend.api.v1.patients import router as patients_router
from backend.api.v1.visits import router as visits_router
from backend.api.v1.deltas import router as deltas_router
from backend.api.v1.scores import router as scores_router
from backend.api.v1.evidence import router as evidence_router
from backend.api.v1.reasoning import router as reasoning_router
from backend.api.v1.extraction import router as extraction_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(patients_router)
api_v1_router.include_router(visits_router)
api_v1_router.include_router(deltas_router)
api_v1_router.include_router(scores_router)
api_v1_router.include_router(evidence_router)
api_v1_router.include_router(reasoning_router)
api_v1_router.include_router(extraction_router)
