from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.models.visit import Visit

class Patient(Base, TimestampMixin):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    synthetic_cohort_label: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    date_of_birth: Mapped[str | None] = mapped_column(String(32), nullable=True)
    population_ethnicity_tag: Mapped[str | None] = mapped_column(String(64), nullable=True, default="asian_south_asian")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    visits: Mapped[List["Visit"]] = relationship(
        "Visit", 
        back_populates="patient", 
        cascade="all, delete-orphan",
        order_by="Visit.visit_number"
    )
