import uuid
from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field
from backend.schemas.common import DomainType, ObservationSource, SourceConfidence

class ExtractedObservationItem(BaseModel):
    domain: DomainType
    parameter: str
    value: Union[float, str]
    numeric_value: Optional[float] = None
    unit: str = ""
    date: str = "2026-09-20"
    source: ObservationSource = ObservationSource.LabReport
    source_confidence: SourceConfidence = SourceConfidence.High
    flag: Optional[str] = None
    reference_range: Optional[str] = None
    notes: Optional[str] = None

class ExtractedValueReviewItem(BaseModel):
    mapped_field: Optional[str] = None
    raw_label: str
    value: Optional[float] = None # Canonical converted value
    unit: str = ""                # Reported unit
    canonical_unit: str = ""      # Target standard unit
    original_value: Optional[Union[float, str]] = None
    confidence: str = "high"      # "high" | "medium" | "low"
    source_confidence_reason: str = "Extracted directly from digital text"
    report_reference_range: Optional[str] = None
    domain: Optional[DomainType] = None
    flag: Optional[str] = None
    is_duplicate: bool = False
    range_check_passed: bool = True

class UnmappedLabLine(BaseModel):
    raw_label: str
    raw_value: Optional[str] = None
    notes: str = "Unmapped parameter. Requires clinician review or alias mapping update."

class FlaggedReviewItem(BaseModel):
    mapped_field: Optional[str] = None
    raw_label: str
    reported_value: Any
    reason: str
    suggested_action: str

class ExtractionResult(BaseModel):
    extraction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_method: str = "text_pdf" # "text_pdf" | "ocr" | "free_text"
    extracted_text_preview: str = ""
    confidence: str = "high"        # "high" | "medium" | "low"
    needs_clinician_review: bool = False
    extracted_values: List[ExtractedValueReviewItem] = Field(default_factory=list)
    unmapped_lines: List[UnmappedLabLine] = Field(default_factory=list)
    flagged_for_review: List[FlaggedReviewItem] = Field(default_factory=list)
    dates_detected: List[str] = Field(default_factory=list)
    date_warning: Optional[str] = None
    clinical_notice: str = (
        "Clinical Decision Support Notice: Stated report reference ranges are preserved for clinician review. "
        "Domain severity and longitudinal trend scores evaluate against standardized clinical guideline thresholds."
    )
    # Backward compatibility fields
    observations: List[ExtractedObservationItem] = Field(default_factory=list)
    source_type: Optional[str] = None
    extraction_method: Optional[str] = None
