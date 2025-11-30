"""Session monitoring model."""
from typing import TYPE_CHECKING, Any
from datetime import datetime
from sqlalchemy import String, BigInteger, DateTime, func, ForeignKey, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .attempt import Attempt


class AttemptSession(Base):
    """Attempt session model (UNLOGGED table in database for performance)."""
    __tablename__ = "attempt_sessions"

    attempt_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    college_id: Mapped[int] = mapped_column(ForeignKey("colleges.id"), primary_key=True, index=True)  # For partition pruning
    last_heartbeat: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    client_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    browser_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tab_visible: Mapped[bool] = mapped_column(default=True, nullable=True)
    tab_switch_count: Mapped[int] = mapped_column(default=0, nullable=True)
    focus_lost_count: Mapped[int] = mapped_column(default=0, nullable=True)
    fullscreen_exits: Mapped[int] = mapped_column(default=0, nullable=True)
    copy_paste_count: Mapped[int] = mapped_column(default=0, nullable=True)
    right_click_count: Mapped[int] = mapped_column(default=0, nullable=True)
    suspicious_activity_flags: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        ForeignKeyConstraint(
            ["attempt_id", "college_id"],
            ["attempts.id", "attempts.college_id"],
            ondelete="CASCADE"
        ),
    )

    # Relationships
    # Note: Since attempt_id is part of the primary key, this is a one-to-one relationship
    # We need to specify remote_side to tell SQLAlchemy that Attempt.id and Attempt.college_id
    # are the "remote" (parent) side of the relationship
    attempt: Mapped["Attempt"] = relationship(
        back_populates="attempt_session",
        primaryjoin="and_(AttemptSession.attempt_id == Attempt.id, AttemptSession.college_id == Attempt.college_id)",
        foreign_keys="[AttemptSession.attempt_id, AttemptSession.college_id]",
        remote_side="[Attempt.id, Attempt.college_id]"
    )

