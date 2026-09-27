from typing import TYPE_CHECKING
from sqlalchemy import String, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.models.visit import Visit

class DomainObservation(Base, TimestampMixin):
    __tablename__ = "domain_observations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    visit_id: Mapped[str] = mapped_column(String(64), ForeignKey("visits.id", ondelete="CASCADE"), nullable=False, index=True)
    
    domain: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # Reproductive, Hyperandrogenism, Metabolic, Lifestyle, Psychological, Sleep, Other
    
    parameter_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    
    # Values
    numeric_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    text_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit: Mapped[str] = mapped_column(String(32), default="")
    date: Mapped[str] = mapped_column(String(32), nullable=False)
    
    # Source & Confidence
    source: Mapped[str] = mapped_column(String(64), default="Clinician entry")
    # 'Self report' | 'Lab report' | 'Clinician entry' | 'Computed' | 'OCR-extracted'
    source_confidence: Mapped[str] = mapped_column(String(64), default="high")
    # 'high' | 'low_ocr_review_needed'
    
    # Section 3B: Tri-state missing data tracking
    measurement_status: Mapped[str] = mapped_column(String(32), default="VALUE_PRESENT")
    # 'VALUE_PRESENT' | 'NOT_MEASURED' | 'NOT_APPLICABLE'
    reason_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # e.g., 'not_ordered', 'patient_declined', 'test_contraindicated', 'not_applicable_male_pattern'
    
    # Clinical categorization
    reference_range: Mapped[str | None] = mapped_column(String(64), nullable=True)
    flag: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # 'normal' | 'borderline' | 'elevated' | 'low' | 'abnormal'
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    visit: Mapped["Visit"] = relationship("Visit", back_populates="observations")
