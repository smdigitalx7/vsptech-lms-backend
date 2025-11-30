"""Database models."""

# Base
from .base import Base

# Enums
from .enums import (
    CollegeStatusEnum,
    UserStatusEnum,
    TestStatusEnum,
    AssignmentStatusEnum,
    TestLinkStatusEnum,
    RegistrationStatusEnum,
    AttemptStatusEnum,
    AttemptStateEnum,
    AnswerTypeEnum,
    SubmissionTypeEnum,
    MediaTypeEnum,
    QuestionDifficultyEnum,
    OptionContentTypeEnum,
)

# Core entities
from .college import College, CollegeUser
from .user import User, Role, UserRole
from .section_type import SectionType

# Test management
from .test import Test, Section, Question, QuestionOption, QuestionMedia
from .special_questions import CommunicationQuestion, CodingQuestion

# Assignments and links
from .assignment import Assignment, TestLink

# Student flow
from .registration import Registration
from .attempt import (
    Attempt,
    AttemptAnswer,
    AttemptTextAnswer,
    AttemptAudioAnswer,
    AttemptCodingAnswer,
)

# Session and submission
from .session import AttemptSession
from .submission import Submission

# Views
from .views import AdminTestView, StudentTestView

__all__ = [
    # Base
    "Base",
    # Enums
    "CollegeStatusEnum",
    "UserStatusEnum",
    "TestStatusEnum",
    "AssignmentStatusEnum",
    "TestLinkStatusEnum",
    "RegistrationStatusEnum",
    "AttemptStatusEnum",
    "AttemptStateEnum",
    "AnswerTypeEnum",
    "SubmissionTypeEnum",
    "MediaTypeEnum",
    "QuestionDifficultyEnum",
    "OptionContentTypeEnum",
    # Core entities
    "College",
    "CollegeUser",
    "User",
    "Role",
    "UserRole",
    "SectionType",
    # Test management
    "Test",
    "Section",
    "Question",
    "QuestionOption",
    "QuestionMedia",
    "CommunicationQuestion",
    "CodingQuestion",
    # Assignments
    "Assignment",
    "TestLink",
    # Student flow
    "Registration",
    "Attempt",
    "AttemptAnswer",
    "AttemptTextAnswer",
    "AttemptAudioAnswer",
    "AttemptCodingAnswer",
    # Session and submission
    "AttemptSession",
    "Submission",
    # Views
    "AdminTestView",
    "StudentTestView",
]
