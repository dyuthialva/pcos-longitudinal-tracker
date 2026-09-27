from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, Text, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.models.patient import Patient
    from backend.models.observation import DomainObservation
    from backend.models.delta import ClinicalDeltaModel
    from backend.models.score import DomainScoreModel

class Visit(Base, TimestampMixin):
    __tablename__ = "visits"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    patient_id: Mapped[str] = mapped_column(String(64), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    visit_number: Mapped[int] = mapped_column(Integer, nullable=False)
    visit_date: Mapped[str] = mapped_column(String(32), nullable=False, index=True) # YYYY-MM-DD
    source_type: Mapped[str] = mapped_column(String(128), default="Comprehensive Clinical Encounter")
    data_completeness: Mapped[float] = mapped_column(Float, default=100.0) # 0 to 100
    reasoning_narrative: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="visits")
    observations: Mapped[List["DomainObservation"]] = relationship(
        "DomainObservation", 
        back_populates="visit", 
        cascade="all, delete-orphan"
    )
    deltas: Mapped[List["ClinicalDeltaModel"]] = relationship(
        "ClinicalDeltaModel", 
        back_populates="visit", 
        cascade="all, delete-orphan"
    )
    domain_scores: Mapped[List["DomainScoreModel"]] = relationship(
        "DomainScoreModel", 
        back_populates="visit", 
        cascade="all, delete-orphan"
    )
