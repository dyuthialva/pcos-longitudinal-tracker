from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.patient_service import PatientService
from backend.models.observation import DomainObservation
from backend.schemas.common import DecisionSupportBanner

router = APIRouter(tags=["Evidence"])

@router.get("/patients/{patient_id}/visits/{visit_id}/evidence/{domain}")
def get_domain_evidence(patient_id: str, visit_id: str, domain: str, db: Session = Depends(get_db)):
    service = PatientService(db)
    visit = service.get_visit(patient_id, visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found.")

    service.ensure_visit_computations(visit)

    # Fetch observations for this domain
    domain_clean = domain.capitalize()
    obs_records = (
        db.query(DomainObservation)
        .filter(
            DomainObservation.visit_id == visit.id,
            DomainObservation.domain.ilike(domain_clean)
        )
        .all()
    )

    score_record = next((s for s in visit.domain_scores if s.domain.lower() == domain.lower()), None)
    citations = service.scoring_engine.get_guideline_citations()

    evidence_items = [
        {
            "id": o.id,
            "domain": o.domain,
            "parameter": o.parameter_name,
            "value": o.numeric_value if o.numeric_value is not None else (o.text_value or ""),
            "numericValue": o.numeric_value,
            "unit": o.unit,
            "date": o.date,
            "source": o.source,
            "sourceConfidence": o.source_confidence,
            "measurementStatus": o.measurement_status,
            "reasonCode": o.reason_code,
            "referenceRange": o.reference_range,
            "flag": o.flag,
            "notes": o.notes,
        }
        for o in obs_records
    ]

    return {
        "decision_support": DecisionSupportBanner(),
        "patient_id": patient_id,
        "visit_id": visit.id,
        "domain": domain_clean,
        "citation": citations.get(domain_clean, "2023 International PCOS Guideline"),
        "domain_score": score_record.score if score_record else None,
        "band": score_record.band if score_record else "Insufficient Data",
        "completeness_ratio": score_record.completeness_ratio if score_record else 0.0,
        "missing_fields": score_record.missing_fields if score_record else [],
        "total_observations": len(evidence_items),
        "evidence": evidence_items
    }
