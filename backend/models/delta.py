from typing import TYPE_CHECKING
from sqlalchemy import String, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.models.visit import Visit

class ClinicalDeltaModel(Base, TimestampMixin):
    __tablename__ = "clinical_deltas"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    visit_id: Mapped[str] = mapped_column(String(64), ForeignKey("visits.id", ondelete="CASCADE"), nullable=False, index=True)
    
    domain: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    parameter: Mapped[str] = mapped_column(String(128), nullable=False)
    
    previous_value: Mapped[str | None] = mapped_column(String(64), nullable=True)
    current_value: Mapped[str] = mapped_column(String(64), nullable=False)
    
    delta_display: Mapped[str] = mapped_column(String(64), nullable=False)
    numeric_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(32), default="")
    
    direction: Mapped[str] = mapped_column(String(32), default="neutral") # 'up' | 'down' | 'neutral' | 'changed'
    is_significant: Mapped[bool] = mapped_column(Boolean, default=False)
    
    status_tag: Mapped[str] = mapped_column(String(64), default="Stable")
    # 'Threshold crossed' | 'Moderate change' | 'Substantial shift' | 'Stable' | 'New observation' | 'Attention required' | 'insufficient_history'
    
    status_severity: Mapped[str] = mapped_column(String(32), default="neutral") # 'neutral' | 'moderate' | 'high'
    clinical_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    @property
    def is_meaningful(self) -> bool:
        return self.is_significant

    @is_meaningful.setter
    def is_meaningful(self, value: bool) -> None:
        self.is_significant = value

    def __init__(self, **kwargs):
        if "is_meaningful" in kwargs and "is_significant" not in kwargs:
            kwargs["is_significant"] = kwargs.pop("is_meaningful")
        super().__init__(**kwargs)

    # Relationship
    visit: Mapped["Visit"] = relationship("Visit", back_populates="deltas")
