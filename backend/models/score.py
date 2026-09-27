from typing import TYPE_CHECKING
from sqlalchemy import String, Float, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.models.visit import Visit

class DomainScoreModel(Base, TimestampMixin):
    __tablename__ = "domain_scores"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    visit_id: Mapped[str] = mapped_column(String(64), ForeignKey("visits.id", ondelete="CASCADE"), nullable=False, index=True)
    
    domain: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # Reproductive, Hyperandrogenism, Metabolic, Lifestyle, Psychological, Sleep
    
    score: Mapped[float | None] = mapped_column(Float, nullable=True) # Null if insufficient data
    band: Mapped[str] = mapped_column(String(32), nullable=False) # 'Low' | 'Moderate' | 'Moderate-High' | 'High' | 'Insufficient Data'
    
    severity_component: Mapped[float | None] = mapped_column(Float, nullable=True)
    trend_component: Mapped[float | None] = mapped_column(Float, nullable=True)
    symptoms_component: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Section 3B: Missing data completeness tracking
    completeness_ratio: Mapped[float] = mapped_column(Float, default=1.0)
    confidence: Mapped[str] = mapped_column(String(32), default="full") # 'full' | 'partial' | 'insufficient_data'
    missing_fields: Mapped[list | None] = mapped_column(JSON, default=list)
    
    is_insufficient_data: Mapped[bool] = mapped_column(Boolean, default=False)
    insufficient_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    contributing_parameters: Mapped[list | None] = mapped_column(JSON, default=list)
    meaningful_deltas_count: Mapped[int] = mapped_column(default=0)
    observation_count: Mapped[int] = mapped_column(default=0)
    
    # Configuration transparency
    weights_used: Mapped[dict | None] = mapped_column(JSON, default=dict)
    computed_without_trend: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationship
    visit: Mapped["Visit"] = relationship("Visit", back_populates="domain_scores")
