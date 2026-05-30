from sqlalchemy import Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class ScoringConfig(Base):
    __tablename__ = "scoring_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    weight_credibility: Mapped[float] = mapped_column(Float, default=0.35)
    weight_novelty: Mapped[float] = mapped_column(Float, default=0.25)
    weight_impact: Mapped[float] = mapped_column(Float, default=0.35)
    weight_speed: Mapped[float] = mapped_column(Float, default=0.05)
