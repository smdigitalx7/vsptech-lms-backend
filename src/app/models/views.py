"""Database view models."""
from typing import Any
from sqlalchemy import Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class AdminTestView(Base):
    """Admin test view - Returns complete test data with all fields including answers.
    
    Usage: SELECT test_data FROM admin_test_view WHERE test_id = 1;
    """
    __tablename__ = "admin_test_view"
    __table_args__ = {"info": {"is_view": True}}  # Mark as view, not a table

    test_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    test_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


class StudentTestView(Base):
    """Student test view - Returns test data without sensitive fields (answers, solutions, etc.).
    
    Usage: SELECT test_data FROM student_test_view WHERE test_id = 1;
    Only shows PUBLISHED tests.
    """
    __tablename__ = "student_test_view"
    __table_args__ = {"info": {"is_view": True}}  # Mark as view, not a table

    test_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    test_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

