from typing import Optional, Union, Literal
from pydantic import BaseModel, Field, ConfigDict
from backend.schemas.common import DomainType

class DeltaOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    domain: DomainType
    parameter: str
    previous_value: Optional[Union[float, str]] = Field(None, alias="previousValue")
    current_value: Union[float, str] = Field(..., alias="currentValue")
    delta_display: str = Field(..., alias="deltaDisplay")
    numeric_delta: Optional[float] = Field(None, alias="numericDelta")
    unit: str = ""
    direction: Literal["up", "down", "neutral", "changed"] = "neutral"
    status_tag: str = Field("Stable", alias="statusTag")
    # 'Threshold crossed' | 'Moderate change' | 'Substantial shift' | 'Stable' | 'New observation' | 'Attention required' | 'insufficient_history'
    status_severity: Literal["neutral", "moderate", "high"] = Field("neutral", alias="statusSeverity")
    is_meaningful: bool = Field(False, alias="isMeaningful")
    clinical_note: Optional[str] = Field(None, alias="clinicalNote")

    def to_frontend_dict(self) -> dict:
        return {
            "id": self.id,
            "domain": self.domain.value,
            "parameter": self.parameter,
            "previousValue": self.previous_value,
            "currentValue": self.current_value,
            "deltaDisplay": self.delta_display,
            "numericDelta": self.numeric_delta,
            "unit": self.unit,
            "direction": self.direction,
            "statusTag": self.status_tag,
            "statusSeverity": self.status_severity,
            "isMeaningful": self.is_meaningful,
            "clinicalNote": self.clinical_note,
        }
