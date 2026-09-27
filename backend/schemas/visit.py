from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from backend.schemas.observation import ObservationCreate, ObservationOut
from backend.schemas.delta import DeltaOut
from backend.schemas.score import DomainScoreOut
from backend.schemas.common import DataCompletenessInfo, DecisionSupportBanner
from backend.schemas.extraction import ExtractedObservationItem

class VisitCreate(BaseModel):
    visit_date: str = Field(..., description="YYYY-MM-DD")
    source_type: str = "Comprehensive Clinical Encounter"
    observations: List[ObservationCreate] = Field(default_factory=list, description="Structured form observations")
    free_text_notes: Optional[str] = None
    confirm_extracted: bool = Field(False, description="Set to True to commit pending extracted observations")
    extracted_observations_to_confirm: Optional[List[ObservationCreate]] = Field(
        None, 
        description="Confirmed extracted observations from lab PDF or notes to be committed"
    )

class VisitCreateResponse(BaseModel):
    decision_support: DecisionSupportBanner = Field(default_factory=DecisionSupportBanner)
    visit_id: str
    patient_id: str
    visit_number: int
    visit_date: str
    source_type: str
    is_first_visit: bool
    total_observations_recorded: int
    observations: List[ObservationOut] = Field(default_factory=list)
    domain_completeness: Dict[str, DataCompletenessInfo]
    pending_confirmation_data: Optional[List[ExtractedObservationItem]] = None
    warning: Optional[str] = None
    notice: str = "Visit snapshot created successfully. Visits are immutable records."

class ConfirmExtractionRequest(BaseModel):
    extraction_id: Optional[str] = None
    source_method: str = "text_pdf" # "text_pdf" | "ocr"
    confirmed_observations: List[ObservationCreate] = Field(..., description="Confirmed or corrected extracted observations")
    recompute_scores: bool = True

class ConfirmExtractionResponse(BaseModel):
    decision_support: DecisionSupportBanner = Field(default_factory=DecisionSupportBanner)
    visit_id: str
    patient_id: str
    confirmed_observations_count: int
    source_method: str
    message: str = "Extracted observations confirmed and committed to visit record."
    visit: Dict[str, Any]

class VisitOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    patient_id: str = Field(..., alias="patientId")
    visit_number: int = Field(..., alias="visitNumber")
    date: str
    source_type: str = Field(..., alias="sourceType")
    total_observations: int = Field(0, alias="totalObservations")
    meaningful_changes_count: int = Field(0, alias="meaningfulChangesCount")
    data_completeness: float = Field(100.0, alias="dataCompleteness")
    reasoning_narrative: str = Field("", alias="reasoningNarrative")
    domain_scores: Dict[str, DomainScoreOut] = Field(default_factory=dict, alias="domainScores")
    deltas: List[DeltaOut] = Field(default_factory=list)
    observations: List[ObservationOut] = Field(default_factory=list)
    completeness_by_domain: Optional[Dict[str, DataCompletenessInfo]] = None

    def to_frontend_dict(self) -> dict:
        return {
            "id": self.id,
            "visitNumber": self.visit_number,
            "date": self.date,
            "sourceType": self.source_type,
            "totalObservations": len(self.observations),
            "meaningfulChangesCount": sum(1 for d in self.deltas if d.is_meaningful),
            "dataCompleteness": self.data_completeness,
            "reasoningNarrative": self.reasoning_narrative or "",
            "domainScores": {k: v.to_frontend_dict() for k, v in self.domain_scores.items()},
            "deltas": [d.to_frontend_dict() for d in self.deltas],
            "observations": [o.to_frontend_dict() for o in self.observations],
        }
