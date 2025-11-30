"""Registration model."""
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, BigInteger, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from .enums import RegistrationStatusEnum, registration_status_enum

if TYPE_CHECKING:
    from .assignment import TestLink
    from .college import College
    from .user import User
    from .attempt import Attempt

class Registration(Base):
    """Registration model."""
    __tablename__ = "registrations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    test_link_id: Mapped[int] = mapped_column(ForeignKey("test_links.id"), nullable=False, index=True)
    college_id: Mapped[int] = mapped_column(ForeignKey("colleges.id"), nullable=False, index=True)  # Denormalized for partitioning
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(15), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    roll_number: Mapped[str] = mapped_column(String(50), nullable=False)
    academic_year: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[RegistrationStatusEnum] = mapped_column(registration_status_enum, default=RegistrationStatusEnum.REGISTERED, nullable=False, index=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    test_link: Mapped["TestLink"] = relationship(back_populates="registrations")
    college: Mapped["College"] = relationship(back_populates="registrations")
    user: Mapped["User | None"] = relationship(back_populates="registrations")
    attempts: Mapped[list["Attempt"]] = relationship(back_populates="registration", cascade="all, delete-orphan")

