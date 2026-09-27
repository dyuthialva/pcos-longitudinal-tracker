import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.visit import Visit
from backend.models.observation import DomainObservation
from backend.services.patient_service import PatientService
from backend.services.extraction_service import ExtractionService
from backend.services.scoring_engine import ScoringEngine
from backend.services.reasoning_service import ReasoningService
from backend.schemas.visit import VisitCreate, VisitCreateResponse, ConfirmExtractionRequest, ConfirmExtractionResponse
from backend.schemas.observation import ObservationOut, ObservationCreate
from backend.schemas.extraction import ExtractedObservationItem
from backend.schemas.common import DecisionSupportBanner, MeasurementStatus, ObservationSource, SourceConfidence
from backend.api.v1.patients import serialize_visit_for_frontend

from fastapi import APIRouter, Depends, HTTPException, Request

router = APIRouter(tags=["Visits"])

@router.get("/patients/{patient_id}/visits")
def list_patient_visits(patient_id: str, db: Session = Depends(get_db)):
    service = PatientService(db)
    patient = service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    
    visits = sorted(patient.visits, key=lambda v: v.visit_number)
    return [serialize_visit_for_frontend(v, service) for v in visits]

@router.get("/patients/{patient_id}/visits/{visit_id}")
def get_patient_visit(patient_id: str, visit_id: str, db: Session = Depends(get_db)):
    service = PatientService(db)
    visit = service.get_visit(patient_id, visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found.")
    return serialize_visit_for_frontend(visit, service)

@router.post("/patients/{patient_id}/visits", response_model=VisitCreateResponse, status_code=201)
async def create_patient_visit(
    patient_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Creates a new visit snapshot for an existing patient supporting three input modes:
    1. Structured form observations (JSON or form-data)
    2. Lab PDF upload (extracted first; returns pending confirmation unless confirm_extracted=True)
    3. Free text symptom notes
    """
    service = PatientService(db)
    patient = service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found.")

    content_type = request.headers.get("content-type", "")
    payload: Optional[VisitCreate] = None
    file_bytes: Optional[bytes] = None
    visit_date = ""
    source_type = "Comprehensive Clinical Encounter"
    free_text_notes: Optional[str] = None
    confirm_extracted = False

    if "multipart/form-data" in content_type:
        form = await request.form()
        visit_date = form.get("visit_date") or ""
        source_type = form.get("source_type") or "Comprehensive Clinical Encounter"
        free_text_notes = form.get("free_text_notes") or None
        confirm_extracted = str(form.get("confirm_extracted", "false")).lower() in ["true", "1"]
        uploaded_file = form.get("file")
        if uploaded_file and hasattr(uploaded_file, "read"):
            file_bytes = await uploaded_file.read()
    else:
        try:
            body = await request.json()
            payload = VisitCreate.model_validate(body)
        except Exception as err:
            raise HTTPException(status_code=422, detail=str(err))
        visit_date = payload.visit_date
        source_type = payload.source_type
        free_text_notes = payload.free_text_notes
        confirm_extracted = payload.confirm_extracted

    if not visit_date:
        raise HTTPException(status_code=422, detail="visit_date is required (format: YYYY-MM-DD).")

    # 2. Edge Case Check: Out-of-order visit rejection
    existing_visits = sorted(patient.visits, key=lambda v: v.visit_date)
    if existing_visits:
        latest_visit_date = existing_visits[-1].visit_date
        if visit_date < latest_visit_date:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Out-of-order visit rejected: Visit date '{visit_date}' precedes existing "
                    f"visit date '{latest_visit_date}'. Chronological backfilling is not supported."
                )
            )

    # 3. Edge Case Check: Same-day duplicate warning
    same_day_warning = None
    if any(v.visit_date == visit_date for v in existing_visits):
        same_day_warning = (
            f"Note: A visit record already exists for patient '{patient_id}' on '{visit_date}'. "
            "Proceeding with same-day encounter snapshot."
        )

    # 4. Handle input modes: structured data, lab PDF, free text
    observations_to_commit: List[ObservationCreate] = []
    pending_extracted: List[ExtractedObservationItem] = []

    # Mode 1: Direct structured form fields
    if payload and payload.observations:
        observations_to_commit.extend(payload.observations)

    # Mode 1b: Explicitly confirmed extracted items
    if payload and payload.extracted_observations_to_confirm:
        observations_to_commit.extend(payload.extracted_observations_to_confirm)

    # Mode 2: Lab PDF upload
    if file_bytes:
        extraction_svc = ExtractionService()
        extraction_res = extraction_svc.process_lab_pdf(file_bytes)
        
        if confirm_extracted:
            for item in extraction_res.observations:
                observations_to_commit.append(
                    ObservationCreate(
                        domain=item.domain,
                        parameter=item.parameter,
                        numeric_value=item.numeric_value,
                        text_value=str(item.value),
                        unit=item.unit,
                        date=visit_date,
                        source=item.source,
                        source_confidence=item.source_confidence,
                        measurement_status=MeasurementStatus.VALUE_PRESENT,
                        flag=item.flag
                    )
                )
        else:
            pending_extracted.extend(extraction_res.observations)

    # Mode 3: Free text notes extraction
    if free_text_notes and not confirm_extracted:
        extraction_svc = ExtractionService()
        text_extracted = extraction_svc.extract_with_groq(
            free_text_notes, 
            confidence=SourceConfidence.High
        )
        if text_extracted:
            pending_extracted.extend(text_extracted)

    # 5. Edge Case Check: Zero clinical fields check
    if len(observations_to_commit) == 0:
        if len(pending_extracted) > 0:
            # If PDF/text was extracted, return pending confirmation payload before persisting visit
            scoring_engine = ScoringEngine()
            completeness_preview = {
                d: scoring_engine.evaluate_completeness(d, [])
                for d in ["Reproductive", "Hyperandrogenism", "Metabolic", "Lifestyle", "Psychological", "Sleep"]
            }
            return VisitCreateResponse(
                visit_id=f"preview-v{len(patient.visits) + 1}-{patient_id.lower()}",
                patient_id=patient_id,
                visit_number=len(patient.visits) + 1,
                visit_date=visit_date,
                source_type=source_type,
                is_first_visit=len(patient.visits) == 0,
                total_observations_recorded=0,
                observations=[],
                domain_completeness=completeness_preview,
                pending_confirmation_data=pending_extracted,
                warning=same_day_warning,
                notice=(
                    "Lab PDF / text extracted successfully. Pending clinician confirmation. "
                    "Re-submit with confirm_extracted=True or include confirmed observations to persist visit."
                )
            )
        else:
            raise HTTPException(
                status_code=422,
                detail="At least one clinical parameter must be provided to create a visit snapshot."
            )

    # 6. Persist immutable visit snapshot
    next_num = len(patient.visits) + 1
    new_visit_id = f"v{next_num}-{patient_id.lower()}"

    visit = Visit(
        id=new_visit_id,
        patient_id=patient.id,
        visit_number=next_num,
        visit_date=visit_date,
        source_type=source_type,
        data_completeness=100.0,
        reasoning_narrative=free_text_notes or ""
    )
    db.add(visit)
    db.flush()

    stored_observations: List[DomainObservation] = []
    for item in observations_to_commit:
        obs = DomainObservation(
            id=f"obs-{uuid.uuid4().hex[:12]}",
            visit_id=visit.id,
            domain=item.domain.value,
            parameter_name=item.parameter_name,
            numeric_value=item.numeric_value,
            text_value=item.text_value or (str(item.numeric_value) if item.numeric_value is not None else None),
            unit=item.unit,
            date=item.date or visit_date,
            source=item.source.value,
            source_confidence=item.source_confidence.value,
            measurement_status=item.measurement_status.value,
            reason_code=item.reason_code,
            reference_range=item.reference_range,
            flag=item.flag,
            notes=item.notes
        )
        db.add(obs)
        stored_observations.append(obs)

    db.commit()
    db.refresh(visit)

    # 7. Evaluate domain completeness immediately (Section 3B requirement)
    scoring_engine = ScoringEngine()
    completeness_summary = {
        d: scoring_engine.evaluate_completeness(d, stored_observations)
        for d in ["Reproductive", "Hyperandrogenism", "Metabolic", "Lifestyle", "Psychological", "Sleep"]
    }

    obs_out_list = [
        ObservationOut(
            id=o.id,
            visit_id=o.visit_id,
            domain=o.domain,
            parameter=o.parameter_name,
            numeric_value=o.numeric_value,
            text_value=o.text_value,
            unit=o.unit,
            date=o.date,
            source=o.source,
            source_confidence=o.source_confidence,
            measurement_status=o.measurement_status,
            reason_code=o.reason_code,
            reference_range=o.reference_range,
            flag=o.flag,
            notes=o.notes
        )
        for o in stored_observations
    ]

    return VisitCreateResponse(
        visit_id=visit.id,
        patient_id=patient.id,
        visit_number=visit.visit_number,
        visit_date=visit.visit_date,
        source_type=visit.source_type,
        is_first_visit=(visit.visit_number == 1),
        total_observations_recorded=len(obs_out_list),
        observations=obs_out_list,
        domain_completeness=completeness_summary,
        pending_confirmation_data=pending_extracted if pending_extracted else None,
        warning=same_day_warning,
        notice="Visit snapshot created successfully. Trigger /process to compute deltas, scores, and narrative."
    )

@router.post("/patients/{patient_id}/visits/{visit_id}/process")
def process_visit_downstream(patient_id: str, visit_id: str, db: Session = Depends(get_db)):
    """
    Explicit downstream processing step (Section 5B step 5):
    Triggers delta computation, domain scoring with completeness ratios, and reasoning generation.
    """
    service = PatientService(db)
    visit = service.get_visit(patient_id, visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail=f"Visit '{visit_id}' not found for patient '{patient_id}'.")

    # 1. Delta engine & Scoring engine
    service.ensure_visit_computations(visit)

    # 2. Reasoning engine trigger
    curr_obs = visit.observations
    evidence_dict = {}
    for o in curr_obs:
        if o.measurement_status == "VALUE_PRESENT":
            if o.domain not in evidence_dict:
                evidence_dict[o.domain] = []
            evidence_dict[o.domain].append({
                "parameter": o.parameter_name,
                "value": o.numeric_value if o.numeric_value is not None else o.text_value,
                "unit": o.unit
            })

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
    reasoning_res = reasoning_engine.generate_reasoning(payload)

    if reasoning_res.narrative:
        visit.reasoning_narrative = reasoning_res.narrative
        db.commit()
        db.refresh(visit)

    return serialize_visit_for_frontend(visit, service)

@router.post(
    "/patients/{patient_id}/visits/{visit_id}/confirm-extraction",
    response_model=ConfirmExtractionResponse,
    status_code=200
)
def confirm_visit_extraction(
    patient_id: str,
    visit_id: str,
    payload: ConfirmExtractionRequest,
    db: Session = Depends(get_db)
):
    """
    STEP 6: Commit confirmed lab extraction to visit.
    Takes extraction_id plus confirmed/corrected observations, writes values into visit
    tagged source: 'lab_report' (or 'ocr_extracted'), with preserved confidence score.
    """
    service = PatientService(db)
    visit = service.get_visit(patient_id, visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail=f"Visit '{visit_id}' not found for patient '{patient_id}'.")

    existing_obs_map = {o.parameter_name.lower(): o for o in visit.observations}
    committed_count = 0

    src = ObservationSource.OcrExtracted if payload.source_method == "ocr" else ObservationSource.LabReport
    conf = SourceConfidence.LowOcrReviewNeeded if payload.source_method == "ocr" else SourceConfidence.High

    for item in payload.confirmed_observations:
        param_key = item.parameter_name.lower()
        if param_key in existing_obs_map:
            existing_obs = existing_obs_map[param_key]
            existing_obs.numeric_value = item.numeric_value
            existing_obs.text_value = item.text_value or (str(item.numeric_value) if item.numeric_value is not None else None)
            existing_obs.unit = item.unit
            existing_obs.source = src
            existing_obs.source_confidence = conf
            existing_obs.flag = item.flag or existing_obs.flag
            existing_obs.reference_range = item.reference_range or existing_obs.reference_range
        else:
            new_obs = DomainObservation(
                id=str(uuid.uuid4()),
                visit_id=visit.id,
                domain=item.domain.value if hasattr(item.domain, "value") else str(item.domain),
                parameter_name=item.parameter_name,
                numeric_value=item.numeric_value,
                text_value=item.text_value or (str(item.numeric_value) if item.numeric_value is not None else None),
                unit=item.unit,
                date=visit.visit_date,
                source=src,
                source_confidence=conf,
                measurement_status=item.measurement_status,
                reason_code=item.reason_code,
                reference_range=item.reference_range,
                flag=item.flag,
                notes=item.notes
            )
            db.add(new_obs)
        committed_count += 1

    db.commit()
    db.refresh(visit)

    if payload.recompute_scores:
        service.ensure_visit_computations(visit)

    serialized = serialize_visit_for_frontend(visit, service)

    return ConfirmExtractionResponse(
        visit_id=visit.id,
        patient_id=patient_id,
        confirmed_observations_count=committed_count,
        source_method=payload.source_method,
        visit=serialized
    )

