from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.patient_service import PatientService
from backend.config.settings import load_scoring_config
from backend.schemas.common import DecisionSupportBanner

router = APIRouter(tags=["Scores"])

@router.get("/patients/{patient_id}/visits/{visit_id}/scores")
def get_visit_scores(patient_id: str, visit_id: str, db: Session = Depends(get_db)):
    service = PatientService(db)
    visit = service.get_visit(patient_id, visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found.")

    service.ensure_visit_computations(visit)
    cfg = load_scoring_config()

    domain_scores_dict = {}
    completeness_dict = {}

    for s in visit.domain_scores:
        domain_scores_dict[s.domain] = {
            "domain": s.domain,
            "score": s.score,
            "band": s.band,
            "severityComponent": s.severity_component,
            "trendComponent": s.trend_component,
            "symptomsComponent": s.symptoms_component,
            "isInsufficientData": s.is_insufficient_data,
            "insufficientReason": s.insufficient_reason,
            "contributingParameters": s.contributing_parameters or [],
            "meaningfulDeltasCount": s.meaningful_deltas_count,
            "observationCount": s.observation_count,
            "computedWithoutTrend": s.computed_without_trend,
            "weightsUsed": s.weights_used,
        }

        # Section 3B: data_completeness object per domain
        completeness_dict[s.domain] = {
            "domain": s.domain,
            "completeness_ratio": s.completeness_ratio,
            "confidence": s.confidence,
            "missing_fields": s.missing_fields or [],
        }

    citations = service.scoring_engine.get_guideline_citations()

    return {
        "decision_support": DecisionSupportBanner(),
        "visit_id": visit.id,
        "patient_id": patient_id,
        "visit_number": visit.visit_number,
        "is_first_visit": visit.visit_number == 1,
        "domain_scores": domain_scores_dict,
        "data_completeness": completeness_dict,
        "scoring_weights": cfg.get("weights", {}),
        "baseline_weights_no_trend": cfg.get("baseline_weights_no_trend", {}),
        "guideline_citations": citations,
        "population_profile_active": cfg.get("population_settings", {}).get("active_profile", "asian_south_asian"),
    }
