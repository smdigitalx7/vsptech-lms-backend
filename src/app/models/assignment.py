"""Assignment and test link models."""
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import DateTime, func, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY as PG_ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func as sql_func
from .base import Base
from .enums import AssignmentStatusEnum, assignment_status_enum, TestLinkStatusEnum, test_link_status_enum

if TYPE_CHECKING:
    from .test import Test
    from .college import College
    from .registration import Registration


class Assignment(Base):
    """Assignment model."""
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"), nullable=False, index=True)
    college_id: Mapped[int] = mapped_column(ForeignKey("colleges.id"), nullable=False, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[AssignmentStatusEnum] = mapped_column(assignment_status_enum, default=AssignmentStatusEnum.SCHEDULED, nullable=False, index=True)
    max_attempts: Mapped[int | None] = mapped_column(default=1, nullable=True)
    grace_period_minutes: Mapped[int] = mapped_column(default=0, nullable=False)
    allow_back_navigation: Mapped[bool] = mapped_column(default=True, nullable=False)
    allowed_ip_ranges: Mapped[list[str] | None] = mapped_column(PG_ARRAY(Text), nullable=True)
    shuffle_questions: Mapped[bool] = mapped_column(default=False, nullable=False)
    shuffle_options: Mapped[bool] = mapped_column(default=False, nullable=False)
    show_results_immediately: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    test: Mapped['Test'] = relationship(back_populates="assignments")
    college: Mapped['College'] = relationship(back_populates="assignments")
    test_links: Mapped[list["TestLink"]] = relationship(back_populates="assignment", cascade="all, delete-orphan")


class TestLink(Base):
    """Test link model."""
    __tablename__ = "test_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"), nullable=False, index=True)
    link_uuid: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), unique=True, nullable=False, index=True, server_default=sql_func.gen_random_uuid())
    status: Mapped[TestLinkStatusEnum] = mapped_column(test_link_status_enum, default=TestLinkStatusEnum.ACTIVE, nullable=False, index=True)
    max_registrations: Mapped[int | None] = mapped_column(nullable=True)  # NULL = unlimited
    current_registrations: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    assignment: Mapped["Assignment"] = relationship(back_populates="test_links")
    registrations: Mapped[list["Registration"]] = relationship(back_populates="test_link", cascade="all, delete-orphan")

