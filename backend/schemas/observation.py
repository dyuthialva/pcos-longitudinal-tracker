from typing import Optional, Union
from pydantic import BaseModel, Field, ConfigDict, model_validator
from backend.schemas.common import (
    DomainType,
    ObservationSource,
    SourceConfidence,
    MeasurementStatus,
)

# Plausible clinical ranges for PCOS decision support
PLAUSIBLE_RANGES = {
    "bmi": (10.0, 80.0, "kg/m2"),
    "weight": (25.0, 300.0, "kg"),
    "waist_circumference": (40.0, 200.0, "cm"),
    "cycle_length": (15.0, 365.0, "days"),
    "cycle_variability_sd": (0.0, 90.0, "days"),
    "missed_periods_count": (0.0, 12.0, "periods"),
    "phq9_score": (0.0, 27.0, "points"),
    "gad7_score": (0.0, 21.0, "points"),
    "fasting_glucose": (30.0, 600.0, "mg/dL"),
    "fasting_insulin": (0.5, 300.0, "uIU/mL"),
    "hba1c": (3.0, 20.0, "%"),
    "systolic_bp": (60.0, 260.0, "mmHg"),
    "diastolic_bp": (30.0, 160.0, "mmHg"),
    "sleep_hours": (0.0, 24.0, "hours"),
    "sleep_quality_score": (1.0, 10.0, "points"),
    "diet_quality_score": (1.0, 10.0, "points"),
    "activity_minutes_week": (0.0, 2000.0, "min/week"),
    "hirsutism_mfg_score": (0.0, 36.0, "points"),
    "total_testosterone": (0.01, 15.0, "ng/mL"),
    "free_testosterone": (0.1, 50.0, "pg/mL"),
    "dheas": (10.0, 1500.0, "ug/dL"),
    "shbg": (5.0, 300.0, "nmol/L"),
}

class ObservationBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    domain: DomainType
    parameter_name: str = Field(..., alias="parameter")
    numeric_value: Optional[float] = Field(None, alias="numericValue")
    text_value: Optional[str] = Field(None, alias="textValue")
    unit: str = ""
    date: Optional[str] = None
    source: ObservationSource = ObservationSource.ClinicianEntry
    source_confidence: SourceConfidence = SourceConfidence.High
    measurement_status: MeasurementStatus = MeasurementStatus.VALUE_PRESENT
    reason_code: Optional[str] = None
    reference_range: Optional[str] = Field(None, alias="referenceRange")
    flag: Optional[str] = None
    notes: Optional[str] = None

class ObservationCreate(ObservationBase):
    @model_validator(mode="after")
    def validate_clinical_plausibility(self):
        # Only validate range when value is present and numeric
        if self.measurement_status == MeasurementStatus.VALUE_PRESENT and self.numeric_value is not None:
            param = self.parameter_name.lower().replace(" ", "_")
            if param in PLAUSIBLE_RANGES:
                min_v, max_v, expected_unit = PLAUSIBLE_RANGES[param]
                if not (min_v <= self.numeric_value <= max_v):
                    raise ValueError(
                        f"Plausibility check failed for {param}: {self.numeric_value} is outside "
                        f"valid biological range [{min_v}, {max_v}] ({expected_unit})."
                    )
        return self

class ObservationOut(ObservationBase):
    id: str
    visit_id: str = Field(..., alias="visitId")
    date: str
    
    # Direct accessor for frontend display
    @property
    def value(self) -> Union[float, str]:
        if self.numeric_value is not None:
            return self.numeric_value
        return self.text_value or ""

    def to_frontend_dict(self) -> dict:
        return {
            "id": self.id,
            "domain": self.domain.value,
            "parameter": self.parameter_name,
            "value": self.numeric_value if self.numeric_value is not None else (self.text_value or ""),
            "numericValue": self.numeric_value,
            "unit": self.unit,
            "date": self.date,
            "source": self.source.value,
            "sourceConfidence": self.source_confidence.value,
            "measurementStatus": self.measurement_status.value,
            "reasonCode": self.reason_code,
            "visitId": self.visit_id,
            "referenceRange": self.reference_range,
            "flag": self.flag,
            "notes": self.notes,
        }
