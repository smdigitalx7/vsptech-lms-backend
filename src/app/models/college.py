"""College models."""
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from .enums import CollegeStatusEnum, college_status_enum

if TYPE_CHECKING:
    from .assignment import Assignment
    from .registration import Registration
    from .user import User


class College(Base):
    """College model."""
    __tablename__ = "colleges"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[CollegeStatusEnum] = mapped_column(college_status_enum, default=CollegeStatusEnum.ACTIVE, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    # Relationships
    college_users: Mapped[list["CollegeUser"]] = relationship(back_populates="college", cascade="all, delete-orphan")
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="college", cascade="all, delete-orphan")
    registrations: Mapped[list["Registration"]] = relationship(back_populates="college", cascade="all, delete-orphan")


class CollegeUser(Base):
    """College-User many-to-many relationship."""
    __tablename__ = "college_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    college_id: Mapped[int] = mapped_column(ForeignKey("colleges.id", ondelete="CASCADE"), nullable=False, index=True)
    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="college_users")
    college: Mapped["College"] = relationship(back_populates="college_users")

    __table_args__ = (
        UniqueConstraint("user_id", "college_id", name="uq_college_users_user_college"),
    )

