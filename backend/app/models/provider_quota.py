from datetime import datetime, UTC

from sqlalchemy import Integer, String, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProviderQuota(Base):
    __tablename__ = "provider_quotas"
    __table_args__ = (
        UniqueConstraint("provider_name", "quota_window", name="uq_provider_quota_window"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    provider_name: Mapped[str] = mapped_column(String(120), index=True)
    quota_window: Mapped[str] = mapped_column(String(40), default="daily") # e.g. "daily", "monthly", "minute"
    estimated_quota: Mapped[int] = mapped_column(Integer, default=0)
    calls_used: Mapped[int] = mapped_column(Integer, default=0)
    last_successful_call: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_safe_refresh: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def is_exhausted(self) -> bool:
        if self.estimated_quota <= 0:
            return False
        return self.calls_used >= self.estimated_quota

    def can_call(self) -> bool:
        if self.is_exhausted():
            return False
        if self.next_safe_refresh and datetime.now(UTC) < self.next_safe_refresh.replace(tzinfo=UTC):
            return False
        return True
