"""Database ENUM types."""
from enum import Enum
from sqlalchemy import Enum as SQLEnum


class CollegeStatusEnum(str, Enum):
    """College status enum."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class UserStatusEnum(str, Enum):
    """User status enum."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    LOCKED = "LOCKED"
    SUSPENDED = "SUSPENDED"


class TestStatusEnum(str, Enum):
    """Test status enum."""
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class AssignmentStatusEnum(str, Enum):
    """Assignment status enum."""
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TestLinkStatusEnum(str, Enum):
    """Test link status enum."""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    INVALIDATED = "INVALIDATED"


class RegistrationStatusEnum(str, Enum):
    """Registration status enum."""
    REGISTERED = "REGISTERED"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"


class AttemptStatusEnum(str, Enum):
    """Attempt status enum."""
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    AUTO_SUBMITTED = "AUTO_SUBMITTED"
    EXPIRED = "EXPIRED"


class AttemptStateEnum(str, Enum):
    """Attempt state enum (for monitoring)."""
    ACTIVE = "ACTIVE"
    IDLE = "IDLE"
    DISCONNECTED = "DISCONNECTED"
    SUBMITTED = "SUBMITTED"


class AnswerTypeEnum(str, Enum):
    """Answer type enum."""
    MCQ = "MCQ"
    CODING = "CODING"
    AUDIO = "AUDIO"
    TEXT = "TEXT"


class SubmissionTypeEnum(str, Enum):
    """Submission type enum."""
    MANUAL = "MANUAL"
    AUTO_SUBMIT = "AUTO_SUBMIT"
    FORCE_SUBMIT = "FORCE_SUBMIT"


class MediaTypeEnum(str, Enum):
    """Media type enum."""
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"


class QuestionDifficultyEnum(str, Enum):
    """Question difficulty enum."""
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    EXPERT = "EXPERT"


class OptionContentTypeEnum(str, Enum):
    """Option content type enum."""
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"


# SQLAlchemy Enum types that reference existing database enum types
college_status_enum = SQLEnum(
    "ACTIVE", "INACTIVE", "SUSPENDED",
    name="college_status_enum",
    create_type=False
)

user_status_enum = SQLEnum(
    "ACTIVE", "INACTIVE", "LOCKED", "SUSPENDED",
    name="user_status_enum",
    create_type=False
)

test_status_enum = SQLEnum(
    "DRAFT", "PUBLISHED", "ARCHIVED",
    name="test_status_enum",
    create_type=False
)

assignment_status_enum = SQLEnum(
    "SCHEDULED", "ACTIVE", "COMPLETED", "CANCELLED",
    name="assignment_status_enum",
    create_type=False
)

test_link_status_enum = SQLEnum(
    "ACTIVE", "EXPIRED", "INVALIDATED",
    name="test_link_status_enum",
    create_type=False
)

registration_status_enum = SQLEnum(
    "REGISTERED", "STARTED", "COMPLETED", "EXPIRED",
    name="registration_status_enum",
    create_type=False
)

attempt_status_enum = SQLEnum(
    "IN_PROGRESS", "SUBMITTED", "AUTO_SUBMITTED", "EXPIRED",
    name="attempt_status_enum",
    create_type=False
)

attempt_state_enum = SQLEnum(
    "ACTIVE", "IDLE", "DISCONNECTED", "SUBMITTED",
    name="attempt_state_enum",
    create_type=False
)

answer_type_enum = SQLEnum(
    "MCQ", "CODING", "AUDIO", "TEXT",
    name="answer_type_enum",
    create_type=False
)

submission_type_enum = SQLEnum(
    "MANUAL", "AUTO_SUBMIT", "FORCE_SUBMIT",
    name="submission_type_enum",
    create_type=False
)

media_type_enum = SQLEnum(
    "IMAGE", "AUDIO", "VIDEO",
    name="media_type_enum",
    create_type=False
)

question_difficulty_enum = SQLEnum(
    "EASY", "MEDIUM", "HARD", "EXPERT",
    name="question_difficulty_enum",
    create_type=False
)

option_content_type_enum = SQLEnum(
    "TEXT", "IMAGE", "AUDIO",
    name="option_content_type_enum",
    create_type=False
)

