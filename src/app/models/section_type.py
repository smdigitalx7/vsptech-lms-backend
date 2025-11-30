"""Section type model."""
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .test import Section


class SectionType(Base):
    """Section type model - determines question behavior."""
    __tablename__ = "section_type"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    requires_options: Mapped[bool] = mapped_column(default=False, nullable=False)
    requires_media: Mapped[bool] = mapped_column(default=False, nullable=False)
    requires_special_table: Mapped[bool] = mapped_column(default=False, nullable=False)
    special_table_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    sections: Mapped[list['Section']] = relationship(back_populates="section_type")

