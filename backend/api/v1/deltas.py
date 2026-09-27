from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.patient_service import PatientService
from backend.schemas.common import DecisionSupportBanner

router = APIRouter(tags=["Deltas"])

@router.get("/patients/{patient_id}/visits/{visit_id}/deltas")
def get_visit_deltas(patient_id: str, visit_id: str, db: Session = Depends(get_db)):
    service = PatientService(db)
    visit = service.get_visit(patient_id, visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found.")

    service.ensure_visit_computations(visit)

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
        for d in visit.deltas
    ]

    return {
        "decision_support": DecisionSupportBanner(),
        "visit_id": visit.id,
        "patient_id": patient_id,
        "is_first_visit": visit.visit_number == 1,
        "total_deltas": len(deltas_list),
        "meaningful_deltas_count": sum(1 for d in deltas_list if d["isMeaningful"]),
        "deltas": deltas_list
    }
