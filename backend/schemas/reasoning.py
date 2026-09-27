from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from backend.schemas.common import DataCompletenessInfo, DecisionSupportBanner

class ReasoningInputPayload(BaseModel):
    patient_id: str
    visit_id: str
    visit_date: str
    is_first_visit: bool = False
    scores: Dict[str, Any]
    deltas: List[Dict[str, Any]]
    evidence: Dict[str, List[Dict[str, Any]]]
    data_completeness: Dict[str, DataCompletenessInfo]

class ReasoningResponse(BaseModel):
    decision_support: DecisionSupportBanner = Field(default_factory=DecisionSupportBanner)
    visit_id: str
    narrative: str
    cited_parameters: List[str] = Field(default_factory=list)
    validation_passed: bool = True
    validation_notes: Optional[str] = None
    insufficient_data_domains: List[str] = Field(default_factory=list)
    partial_domains: Dict[str, List[str]] = Field(default_factory=dict)
