from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DailyBriefSchedule(Base):
    __tablename__ = "daily_brief_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    local_time: Mapped[time] = mapped_column(Time, default=time(7, 0), nullable=False)
    days_of_week: Mapped[list[int]] = mapped_column(
        JSON,
        default=lambda: [0, 1, 2, 3, 4],
        nullable=False,
    )
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_succeeded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_status: Mapped[str] = mapped_column(String(40), default="disabled", nullable=False)
    last_processing_run_id: Mapped[int | None] = mapped_column(ForeignKey("processing_runs.id"))
    last_brief_id: Mapped[int | None] = mapped_column(ForeignKey("daily_briefs.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
