from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.patient import Patient
from backend.models.visit import Visit
from backend.services.patient_service import PatientService
from backend.schemas.patient import PatientCreate, PatientCreateResponse

router = APIRouter(tags=["Patients"])

def serialize_visit_for_frontend(v: Visit, service: PatientService) -> dict:
    service.ensure_visit_computations(v)
    
    # Map domain scores
    domain_scores_dict = {}
    for s in v.domain_scores:
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
        }

    deltas_list = [
        {
            "id": d.id,
            "domain": d.domain,
            "parameter": d.parameter,
            "previousValue": d.previous_value,
            "currentValue": d.current_value,
            "deltaDisplay": d.delta_display,
            "numericDelta": d.numeric_delta,
            "unit": d.unit,
            "direction": d.direction,
            "statusTag": d.status_tag,
            "statusSeverity": d.status_severity,
            "isMeaningful": d.is_meaningful,
            "clinicalNote": d.clinical_note,
        }
        for d in v.deltas
    ]

    obs_list = [
        {
            "id": o.id,
            "domain": o.domain,
            "parameter": o.parameter_name,
            "value": o.numeric_value if o.numeric_value is not None else (o.text_value or ""),
            "numericValue": o.numeric_value,
            "unit": o.unit,
            "date": o.date,
            "source": o.source,
            "visitId": o.visit_id,
            "referenceRange": o.reference_range,
            "flag": o.flag,
            "notes": o.notes,
        }
        for o in v.observations
        if o.measurement_status == "VALUE_PRESENT"
    ]

    meaningful_count = sum(1 for d in deltas_list if d["isMeaningful"])

    return {
        "id": v.id,
        "visitNumber": v.visit_number,
        "date": v.visit_date,
        "sourceType": v.source_type,
        "totalObservations": len(obs_list),
        "meaningfulChangesCount": meaningful_count,
        "dataCompleteness": round(v.data_completeness, 0),
        "reasoningNarrative": v.reasoning_narrative or "",
        "domainScores": domain_scores_dict,
        "deltas": deltas_list,
        "observations": obs_list,
    }

def serialize_patient_for_frontend(p: Patient, service: PatientService) -> dict:
    visits = sorted(p.visits, key=lambda v: v.visit_number)
    serialized_visits = [serialize_visit_for_frontend(v, service) for v in visits]
    first_date = visits[0].visit_date if visits else ""
    latest_date = visits[-1].visit_date if visits else ""

    return {
        "id": p.id,
        "syntheticCohortLabel": p.synthetic_cohort_label,
        "age": p.age,
        "firstVisitDate": first_date,
        "latestVisitDate": latest_date,
        "totalVisits": len(visits),
        "dataCompleteness": 92,
        "lastUpdated": latest_date,
        "notes": p.notes or "",
        "visits": serialized_visits,
    }

@router.get("/patients")
def list_patients(db: Session = Depends(get_db)):
    service = PatientService(db)
    patients = service.list_patients()
    return [serialize_patient_for_frontend(p, service) for p in patients]

@router.post("/patients", response_model=PatientCreateResponse, status_code=201)
def create_patient(data: PatientCreate, db: Session = Depends(get_db)):
    # 1. Resolve or generate patient ID
    if data.id:
        pid = data.id.strip()
        existing = db.query(Patient).filter(Patient.id == pid).first()
        if existing:
            raise HTTPException(
                status_code=409, 
                detail=f"Patient with ID '{pid}' already exists. IDs must be unique."
            )
    else:
        # Generate de-identified synthetic ID
        total_pts = db.query(Patient).count()
        pid = f"P-{total_pts + 101:04d}"

    # 2. Resolve age and reproductive range plausibility check
    resolved_age = data.resolve_age()
    age_warning = None
    if resolved_age < 12 or resolved_age > 55:
        age_warning = (
            f"Note: Patient age ({resolved_age}) is outside standard reproductive age range (12-55). "
            "Proceeding with registration for edge-case longitudinal tracking."
        )

    # 3. Create persistent record
    patient = Patient(
        id=pid,
        synthetic_cohort_label=data.synthetic_cohort_label or "Synthetic Research Cohort",
        age=resolved_age,
        date_of_birth=data.date_of_birth,
        population_ethnicity_tag=data.population_ethnicity_tag or "asian_south_asian",
        notes=data.notes
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    return PatientCreateResponse(
        patient_id=patient.id,
        synthetic_cohort_label=patient.synthetic_cohort_label,
        age=patient.age,
        date_of_birth=patient.date_of_birth,
        population_ethnicity_tag=patient.population_ethnicity_tag,
        created_at=patient.created_at.isoformat(),
        notes=patient.notes,
        age_range_warning=age_warning
    )

@router.get("/patients/{patient_id}")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    service = PatientService(db)
    patient = service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return serialize_patient_for_frontend(patient, service)

@router.get("/patients/{patient_id}/trends")
def get_patient_trends(
    patient_id: str,
    parameter: str = Query(..., description="Parameter name to fetch longitudinal trend for"),
    db: Session = Depends(get_db)
):
    service = PatientService(db)
    patient = service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return service.get_parameter_trend(patient_id, parameter)
