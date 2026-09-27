from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class DomainType(str, Enum):
    Reproductive = "Reproductive"
    Hyperandrogenism = "Hyperandrogenism"
    Metabolic = "Metabolic"
    Lifestyle = "Lifestyle"
    Psychological = "Psychological"
    Sleep = "Sleep"
    Other = "Other"

class AttentionBand(str, Enum):
    Low = "Low"
    Moderate = "Moderate"
    ModerateHigh = "Moderate-High"
    High = "High"
    InsufficientData = "Insufficient Data"

class MeasurementStatus(str, Enum):
    VALUE_PRESENT = "VALUE_PRESENT"
    NOT_MEASURED = "NOT_MEASURED"
    NOT_APPLICABLE = "NOT_APPLICABLE"

class ObservationSource(str, Enum):
    SelfReport = "Self report"
    LabReport = "Lab report"
    ClinicianEntry = "Clinician entry"
    Computed = "Computed"
    OcrExtracted = "OCR-extracted"

class SourceConfidence(str, Enum):
    High = "high"
    LowOcrReviewNeeded = "low_ocr_review_needed"

class ConfidenceLevel(str, Enum):
    Full = "full"
    Partial = "partial"
    InsufficientData = "insufficient_data"

class DataCompletenessInfo(BaseModel):
    domain: DomainType
    completeness_ratio: float = Field(..., ge=0.0, le=1.0)
    confidence: ConfidenceLevel
    missing_fields: List[str] = Field(default_factory=list)
    fields_present_count: int = 0
    fields_expected_count: int = 0

class DecisionSupportBanner(BaseModel):
    notice: str = "Clinical Decision Support Prototype. Not a diagnostic tool."
    decision_support_only: bool = True
