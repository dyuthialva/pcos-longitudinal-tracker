from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.patient_service import PatientService
from backend.services.reasoning_service import ReasoningService
from backend.schemas.reasoning import ReasoningResponse

router = APIRouter(tags=["Reasoning"])

@router.get("/patients/{patient_id}/visits/{visit_id}/reasoning", response_model=ReasoningResponse)
def get_visit_reasoning(patient_id: str, visit_id: str, db: Session = Depends(get_db)):
    service = PatientService(db)
    visit = service.get_visit(patient_id, visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found.")

    service.ensure_visit_computations(visit)

    # Build restricted payload containing ONLY deltas, scores, evidence, and completeness
    scores_dict = {
        s.domain: {
            "score": s.score,
            "band": s.band,
            "severity": s.severity_component,
            "trend": s.trend_component,
            "symptoms": s.symptoms_component,
            "confidence": s.confidence
        }
        for s in visit.domain_scores
    }

    deltas_list = [
        {
            "parameter": d.parameter,
            "domain": d.domain,
            "previous_value": d.previous_value,
            "current_value": d.current_value,
            "delta_display": d.delta_display,
            "numeric_delta": d.numeric_delta,
            "is_meaningful": d.is_meaningful,
            "status_tag": d.status_tag
        }
        for d in visit.deltas
    ]

    completeness_dict = {
        s.domain: {
            "completeness_ratio": s.completeness_ratio,
            "confidence": s.confidence,
            "missing_fields": s.missing_fields or []
        }
        for s in visit.domain_scores
    }

    evidence_dict = {}
    for o in visit.observations:
        if o.measurement_status == "VALUE_PRESENT":
            if o.domain not in evidence_dict:
                evidence_dict[o.domain] = []
            evidence_dict[o.domain].append({
                "parameter": o.parameter_name,
                "value": o.numeric_value if o.numeric_value is not None else o.text_value,
                "unit": o.unit
            })

    payload = {
        "patient_id": patient_id,
        "visit_id": visit.id,
        "visit_date": visit.visit_date,
        "is_first_visit": (visit.visit_number == 1),
        "scores": scores_dict,
        "deltas": deltas_list,
        "evidence": evidence_dict,
        "data_completeness": completeness_dict
    }

    reasoning_engine = ReasoningService()
    result = reasoning_engine.generate_reasoning(payload)
    
    # Cache generated narrative back to visit
    if not visit.reasoning_narrative and result.narrative:
        visit.reasoning_narrative = result.narrative
        db.commit()

    return result
