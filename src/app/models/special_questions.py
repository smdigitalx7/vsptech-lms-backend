"""Special question models (Communication and Coding)."""
from typing import TYPE_CHECKING, Any
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, ARRAY as PG_ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .test import Question


class CommunicationQuestion(Base):
    """Communication question model."""
    __tablename__ = "communication_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    prompt_audio_url: Mapped[str] = mapped_column(String(500), nullable=False)
    prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_keywords: Mapped[list[str] | None] = mapped_column(PG_ARRAY(Text), nullable=True)
    language: Mapped[str] = mapped_column(String(20), default="en", nullable=False)
    min_duration_seconds: Mapped[int | None] = mapped_column(nullable=True)
    max_duration_seconds: Mapped[int | None] = mapped_column(nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    evaluation_criteria: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    scoring_rubric: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    question: Mapped["Question"] = relationship(back_populates="communication_question")


class CodingQuestion(Base):
    """Coding question model."""
    __tablename__ = "coding_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    problem_statement: Mapped[str] = mapped_column(Text, nullable=False)
    sample_input: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    hidden_test_cases: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, default=list, nullable=False)
    public_test_cases: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, default=list, nullable=True)
    supported_languages: Mapped[list[str]] = mapped_column(PG_ARRAY(Text), nullable=False)
    default_language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    starter_code: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    solution_code: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    time_limit: Mapped[int] = mapped_column(default=5, nullable=False)  # in seconds
    memory_limit: Mapped[int] = mapped_column(default=256, nullable=False)  # in MB
    max_execution_time: Mapped[int | None] = mapped_column(default=30, nullable=True)  # in seconds
    allowed_libraries: Mapped[list[str] | None] = mapped_column(PG_ARRAY(Text), nullable=True)
    forbidden_keywords: Mapped[list[str] | None] = mapped_column(PG_ARRAY(Text), nullable=True)
    test_case_weights: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    question: Mapped["Question"] = relationship(back_populates="coding_question")

