from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict, field_validator
from backend.schemas.visit import VisitOut

class PatientCreate(BaseModel):
    id: Optional[str] = Field(None, alias="patient_id", description="Optional de-identified ID, e.g. P-0099")
    synthetic_cohort_label: Optional[str] = Field(
        "Synthetic Research Cohort", 
        alias="syntheticCohortLabel",
        description="Clinical cohort or Rotterdam phenotype tag"
    )
    age: Optional[int] = Field(None, ge=1, le=120, description="Patient age in years")
    date_of_birth: Optional[str] = Field(None, alias="dateOfBirth", description="YYYY-MM-DD")
    population_ethnicity_tag: Optional[str] = Field(
        "asian_south_asian", 
        alias="populationEthnicityTag",
        description="Population profile for BMI/waist thresholds: asian_south_asian or standard_who"
    )
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("id")
    def validate_id_format(cls, v):
        if v is not None:
            v_clean = v.strip()
            # Security & Privacy check: Disallow personal names or email-like identifiers
            if "@" in v_clean or len(v_clean.split()) > 1:
                raise ValueError("Patient ID must be a de-identified alphanumeric code (e.g. P-0042), not personal data.")
            return v_clean
        return v

    def resolve_age(self) -> int:
        if self.age is not None:
            return self.age
        if self.date_of_birth:
            try:
                dob = datetime.strptime(self.date_of_birth, "%Y-%m-%d").date()
                today = date.today()
                return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            except ValueError:
                pass
        return 28 # Default fallback age for synthetic prototype

class PatientCreateResponse(BaseModel):
    patient_id: str
    synthetic_cohort_label: str
    age: int
    date_of_birth: Optional[str] = None
    population_ethnicity_tag: str
    created_at: str
    notes: Optional[str] = None
    age_range_warning: Optional[str] = None
    notice: str = "De-identified synthetic patient record created successfully."

class PatientSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    synthetic_cohort_label: str = Field(..., alias="syntheticCohortLabel")
    age: int
    first_visit_date: str = Field("", alias="firstVisitDate")
    latest_visit_date: str = Field("", alias="latestVisitDate")
    total_visits: int = Field(0, alias="totalVisits")
    data_completeness: float = Field(100.0, alias="dataCompleteness")
    last_updated: str = Field("", alias="lastUpdated")
    notes: Optional[str] = None
    population_ethnicity_tag: Optional[str] = Field("asian_south_asian", alias="populationEthnicityTag")

    def to_frontend_dict(self) -> dict:
        return {
            "id": self.id,
            "syntheticCohortLabel": self.synthetic_cohort_label,
            "age": self.age,
            "firstVisitDate": self.first_visit_date,
            "latestVisitDate": self.latest_visit_date,
            "totalVisits": self.total_visits,
            "dataCompleteness": self.data_completeness,
            "lastUpdated": self.last_updated,
            "notes": self.notes,
            "populationEthnicityTag": self.population_ethnicity_tag,
        }

class PatientDetail(PatientSummary):
    visits: List[VisitOut] = Field(default_factory=list)

    def to_frontend_dict(self) -> dict:
        base = super().to_frontend_dict()
        base["visits"] = [v.to_frontend_dict() for v in self.visits]
        return base
