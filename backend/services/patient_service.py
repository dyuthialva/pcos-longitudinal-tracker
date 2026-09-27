from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.models.patient import Patient
from backend.models.visit import Visit
from backend.models.observation import DomainObservation
from backend.models.delta import ClinicalDeltaModel
from backend.models.score import DomainScoreModel
from backend.services.delta_engine import DeltaEngine
from backend.services.scoring_engine import ScoringEngine

class PatientService:
    def __init__(self, db: Session):
        self.db = db
        self.delta_engine = DeltaEngine()
        self.scoring_engine = ScoringEngine()

    def list_patients(self) -> List[Patient]:
        return self.db.query(Patient).all()

    def get_patient(self, patient_id: str) -> Optional[Patient]:
        return self.db.query(Patient).filter(Patient.id == patient_id).first()

    def get_visit(self, patient_id: str, visit_id: str) -> Optional[Visit]:
        return (
            self.db.query(Visit)
            .filter(Visit.patient_id == patient_id, Visit.id == visit_id)
            .first()
        )

    def ensure_visit_computations(self, visit: Visit) -> Visit:
        """
        Ensures deltas and domain scores are computed and stored for a visit
        based on longitudinal history.
        """
        # Check if deltas already exist
        existing_scores = self.db.query(DomainScoreModel).filter(DomainScoreModel.visit_id == visit.id).all()
        if existing_scores:
            return visit

        # Find previous visit in chronological sequence
        prev_visit = (
            self.db.query(Visit)
            .filter(Visit.patient_id == visit.patient_id, Visit.visit_number < visit.visit_number)
            .order_by(Visit.visit_number.desc())
            .first()
        )

        curr_obs = self.db.query(DomainObservation).filter(DomainObservation.visit_id == visit.id).all()
        prev_obs = (
            self.db.query(DomainObservation).filter(DomainObservation.visit_id == prev_visit.id).all()
            if prev_visit else None
        )

        # 1. Delta engine
        deltas = self.delta_engine.compute_deltas(
            current_visit_id=visit.id,
            current_observations=curr_obs,
            previous_observations=prev_obs
        )
        for d in deltas:
            self.db.add(d)

        # 2. Scoring engine
        scores_dict = self.scoring_engine.compute_domain_scores(
            visit_id=visit.id,
            observations=curr_obs,
            deltas=deltas,
            is_first_visit=(prev_visit is None)
        )
        for s in scores_dict.values():
            self.db.add(s)

        self.db.commit()
        self.db.refresh(visit)
        return visit

    def get_parameter_trend(self, patient_id: str, parameter_name: str) -> List[Dict[str, Any]]:
        visits = (
            self.db.query(Visit)
            .filter(Visit.patient_id == patient_id)
            .order_by(Visit.visit_number.asc())
            .all()
        )

        trend_points = []
        for v in visits:
            obs = (
                self.db.query(DomainObservation)
                .filter(
                    DomainObservation.visit_id == v.id,
                    DomainObservation.parameter_name == parameter_name,
                    DomainObservation.measurement_status == "VALUE_PRESENT"
                )
                .first()
            )
            if obs and obs.numeric_value is not None:
                trend_points.append({
                    "visitDate": v.visit_date,
                    "visitId": v.id,
                    "visitNumber": v.visit_number,
                    "value": obs.numeric_value,
                    "displayValue": f"{obs.numeric_value} {obs.unit}".strip(),
                    "unit": obs.unit,
                    "source": obs.source,
                    "flag": obs.flag,
                    "referenceRange": obs.reference_range
                })

        return trend_points
