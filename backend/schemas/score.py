from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from backend.schemas.common import (
    DomainType,
    AttentionBand,
    DataCompletenessInfo,
    DecisionSupportBanner,
)

class DomainScoreOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    domain: DomainType
    score: Optional[float] = None
    band: AttentionBand
    severity_component: Optional[float] = Field(None, alias="severityComponent")
    trend_component: Optional[float] = Field(None, alias="trendComponent")
    symptoms_component: Optional[float] = Field(None, alias="symptomsComponent")
    is_insufficient_data: bool = Field(False, alias="isInsufficientData")
    insufficient_reason: Optional[str] = Field(None, alias="insufficientReason")
    contributing_parameters: List[str] = Field(default_factory=list, alias="contributingParameters")
    meaningful_deltas_count: int = Field(0, alias="meaningfulDeltasCount")
    observation_count: int = Field(0, alias="observationCount")
    
    # Section 3B additions
    completeness: Optional[DataCompletenessInfo] = None
    computed_without_trend: bool = Field(False, alias="computedWithoutTrend")
    weights_used: Optional[Dict[str, float]] = Field(default_factory=dict, alias="weightsUsed")

    def to_frontend_dict(self) -> dict:
        return {
            "domain": self.domain.value,
            "score": self.score,
            "band": self.band.value,
            "severityComponent": self.severity_component,
            "trendComponent": self.trend_component,
            "symptomsComponent": self.symptoms_component,
            "isInsufficientData": self.is_insufficient_data,
            "insufficientReason": self.insufficient_reason,
            "contributingParameters": self.contributing_parameters,
            "meaningfulDeltasCount": self.meaningful_deltas_count,
            "observationCount": self.observation_count,
        }

class ScoresResponse(BaseModel):
    decision_support: DecisionSupportBanner = Field(default_factory=DecisionSupportBanner)
    visit_id: str
    patient_id: str
    domain_scores: Dict[str, DomainScoreOut]
    data_completeness: Dict[str, DataCompletenessInfo]
    weights_and_thresholds: Dict[str, Any] = Field(default_factory=dict)
    guideline_citations: Dict[str, str] = Field(default_factory=dict)
