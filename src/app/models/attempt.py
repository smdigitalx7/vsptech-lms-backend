"""Attempt and answer models."""
from typing import TYPE_CHECKING, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, BigInteger, DateTime, func, ForeignKey, Numeric, Text, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from .enums import AttemptStatusEnum, attempt_status_enum, AttemptStateEnum, attempt_state_enum, AnswerTypeEnum, answer_type_enum

if TYPE_CHECKING:
    from .registration import Registration
    from .session import AttemptSession
    from .submission import Submission
    from .test import Question


class Attempt(Base):
    """Attempt model (partitioned by college_id in database)."""
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    registration_id: Mapped[int] = mapped_column(ForeignKey("registrations.id"), nullable=False, index=True)
    college_id: Mapped[int] = mapped_column(ForeignKey("colleges.id"), nullable=False, index=True)  # Denormalized for partitioning
    status: Mapped[AttemptStatusEnum] = mapped_column(attempt_status_enum, default=AttemptStatusEnum.IN_PROGRESS, nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_state: Mapped[AttemptStateEnum] = mapped_column(attempt_state_enum, default=AttemptStateEnum.ACTIVE, nullable=False, index=True)
    final_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    attempt_number: Mapped[int] = mapped_column(default=1, nullable=False)

    # Relationships
    registration: Mapped["Registration"] = relationship(back_populates="attempts")
    attempt_answers: Mapped[list["AttemptAnswer"]] = relationship(back_populates="attempt", cascade="all, delete-orphan")
    attempt_session: Mapped["AttemptSession | None"] = relationship(
        back_populates="attempt",
        uselist=False,
        cascade="all, delete-orphan",
        primaryjoin="and_(Attempt.id == AttemptSession.attempt_id, Attempt.college_id == AttemptSession.college_id)",
        foreign_keys="[AttemptSession.attempt_id, AttemptSession.college_id]"
    )
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan"
    )


class AttemptAnswer(Base):
    """Attempt answer model (partitioned by college_id in database)."""
    __tablename__ = "attempt_answers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(nullable=False)
    college_id: Mapped[int] = mapped_column(ForeignKey("colleges.id"), nullable=False, index=True)  # Denormalized for partitioning
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    answer_type: Mapped[AnswerTypeEnum | None] = mapped_column(answer_type_enum, nullable=True)  # NULL until student provides answer
    mcq_answer: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # References question_options.id
    is_marked_for_review: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        ForeignKeyConstraint(
            ["attempt_id", "college_id"],
            ["attempts.id", "attempts.college_id"],
            ondelete="CASCADE"
        ),
    )

    # Relationships
    attempt: Mapped["Attempt"] = relationship(back_populates="attempt_answers")
    question: Mapped["Question"] = relationship(back_populates="attempt_answers")
    # Note: Relationships to text_answer, audio_answer, coding_answer are handled via composite keys
    # Access these through queries using attempt_id, question_id, college_id


class AttemptTextAnswer(Base):
    """Attempt text answer model."""
    __tablename__ = "attempt_text_answers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(nullable=False, index=True)
    college_id: Mapped[int] = mapped_column(ForeignKey("colleges.id"), nullable=False, index=True)
    text_answer: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships - Note: Composite FK relationship handled via application logic
    # attempt_answer relationship would need composite FK which SQLAlchemy handles differently


class AttemptAudioAnswer(Base):
    """Attempt audio answer model."""
    __tablename__ = "attempt_audio_answers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(nullable=False, index=True)
    college_id: Mapped[int] = mapped_column(ForeignKey("colleges.id"), nullable=False, index=True)
    audio_answer_url: Mapped[str] = mapped_column(String(500), nullable=False)
    audio_transcription: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(nullable=True)

    # Relationships - Note: Composite FK relationship handled via application logic


class AttemptCodingAnswer(Base):
    """Attempt coding answer model."""
    __tablename__ = "attempt_coding_answers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(nullable=False, index=True)
    college_id: Mapped[int] = mapped_column(ForeignKey("colleges.id"), nullable=False, index=True)
    coding_answer: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    execution_results: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Relationships - Note: Composite FK relationship handled via application logic

