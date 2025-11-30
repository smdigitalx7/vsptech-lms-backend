"""Test management models."""
from typing import TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, DateTime, func, ForeignKey, Numeric, Text, UniqueConstraint, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from .enums import (
    TestStatusEnum, test_status_enum,
    QuestionDifficultyEnum, question_difficulty_enum,
    OptionContentTypeEnum, option_content_type_enum,
    MediaTypeEnum, media_type_enum
)

if TYPE_CHECKING:
    from .assignment import Assignment
    from .section_type import SectionType
    from .special_questions import CommunicationQuestion, CodingQuestion
    from .attempt import AttemptAnswer


class Test(Base):
    """Test model."""
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    duration: Mapped[int] = mapped_column(nullable=False)  # in minutes
    passing_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    negative_marking: Mapped[bool] = mapped_column(default=False, nullable=False)
    status: Mapped[TestStatusEnum] = mapped_column(test_status_enum, default=TestStatusEnum.DRAFT, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    # Relationships
    sections: Mapped[list['Section']] = relationship(back_populates="test", cascade="all, delete-orphan", order_by="Section.order_index")
    assignments: Mapped[list['Assignment']] = relationship(back_populates="test", cascade="all, delete-orphan")


class Section(Base):
    """Section model."""
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    section_type_id: Mapped[int] = mapped_column(ForeignKey("section_type.id"), nullable=False, index=True)
    time_limit: Mapped[int | None] = mapped_column(nullable=True)  # in minutes
    order_index: Mapped[int] = mapped_column(nullable=False)
    instructions: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    test: Mapped['Test'] = relationship(back_populates="sections")
    section_type: Mapped['SectionType'] = relationship(back_populates="sections")
    questions: Mapped[list['Question']] = relationship(back_populates="section", cascade="all, delete-orphan", order_by="Question.order_index")

    __table_args__ = (
        UniqueConstraint("test_id", "order_index", name="uq_sections_test_order"),
    )


class Question(Base):
    """Question model."""
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1.00"), nullable=False)
    negative_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=True)
    difficulty: Mapped[QuestionDifficultyEnum | None] = mapped_column(question_difficulty_enum, nullable=True, index=True)
    order_index: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    section: Mapped['Section'] = relationship(back_populates="questions")
    question_options: Mapped[list['QuestionOption']] = relationship(back_populates="question", cascade="all, delete-orphan", order_by="QuestionOption.order_index")
    question_media: Mapped[list['QuestionMedia']] = relationship(back_populates="question", cascade="all, delete-orphan", order_by="QuestionMedia.order_index")
    communication_question: Mapped['CommunicationQuestion | None'] = relationship(back_populates="question", uselist=False, cascade="all, delete-orphan")
    coding_question: Mapped['CodingQuestion | None'] = relationship(back_populates="question", uselist=False, cascade="all, delete-orphan")
    attempt_answers: Mapped[list['AttemptAnswer']] = relationship(back_populates="question")

    __table_args__ = (
        UniqueConstraint("section_id", "order_index", name="uq_questions_section_order"),
    )


class QuestionOption(Base):
    """Question option model."""
    __tablename__ = "question_options"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    option_content: Mapped[str] = mapped_column(Text, nullable=False)
    option_content_type: Mapped[OptionContentTypeEnum] = mapped_column(option_content_type_enum, default=OptionContentTypeEnum.TEXT, nullable=False)
    is_correct: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    order_index: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    question: Mapped["Question"] = relationship(back_populates="question_options")

    __table_args__ = (
        UniqueConstraint("question_id", "order_index", name="uq_question_options_question_order"),
    )


class QuestionMedia(Base):
    """Question media model."""
    __tablename__ = "question_media"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    media_type: Mapped[MediaTypeEnum] = mapped_column(media_type_enum, nullable=False)
    media_url: Mapped[str] = mapped_column(String(500), nullable=False)
    order_index: Mapped[int] = mapped_column(default=1, nullable=False)

    # Relationships
    question: Mapped["Question"] = relationship(back_populates="question_media")

