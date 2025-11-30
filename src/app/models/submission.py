"""Submission model."""
from typing import TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from sqlalchemy import BigInteger, DateTime, func, ForeignKey, Numeric, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from .enums import SubmissionTypeEnum, submission_type_enum

if TYPE_CHECKING:
    from .attempt import Attempt


class Submission(Base):
    """Submission model."""
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(nullable=False, index=True)
    college_id: Mapped[int] = mapped_column(ForeignKey("colleges.id"), nullable=False, index=True)
    submission_type: Mapped[SubmissionTypeEnum] = mapped_column(submission_type_enum, nullable=False, index=True)
    total_marks: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    obtained_marks: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["attempt_id", "college_id"],
            ["attempts.id", "attempts.college_id"],
            ondelete="CASCADE"
        ),
    )

    # Relationships
    attempt: Mapped["Attempt"] = relationship(
        back_populates="submissions"
    )

