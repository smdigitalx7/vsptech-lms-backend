"""Enum API endpoints."""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.enum import EnumResponse, EnumValueResponse, AllEnumsResponse
from app.models.enums import (
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

router = APIRouter(prefix="/enums", tags=["Enums"])

# Mapping of enum names to enum classes
ENUM_MAP: dict[str, type] = {
    "CollegeStatusEnum": CollegeStatusEnum,
    "UserStatusEnum": UserStatusEnum,
    "TestStatusEnum": TestStatusEnum,
    "AssignmentStatusEnum": AssignmentStatusEnum,
    "TestLinkStatusEnum": TestLinkStatusEnum,
    "RegistrationStatusEnum": RegistrationStatusEnum,
    "AttemptStatusEnum": AttemptStatusEnum,
    "AttemptStateEnum": AttemptStateEnum,
    "AnswerTypeEnum": AnswerTypeEnum,
    "SubmissionTypeEnum": SubmissionTypeEnum,
    "MediaTypeEnum": MediaTypeEnum,
    "QuestionDifficultyEnum": QuestionDifficultyEnum,
    "OptionContentTypeEnum": OptionContentTypeEnum,
}


def _get_enum_values(enum_class: type) -> list[EnumValueResponse]:
    """Get all values from an enum class."""
    return [
        EnumValueResponse(name=member.name, value=member.value)
        for member in enum_class
    ]


@router.get("", response_model=AllEnumsResponse)
async def get_all_enums() -> AllEnumsResponse:
    """Get all available enums.
    
    Returns a dictionary containing all enum types with their values.
    
    Returns
    -------
    AllEnumsResponse
        Dictionary of all enums with their values.
    """
    enums_dict: dict[str, list[EnumValueResponse]] = {}
    
    for enum_name, enum_class in ENUM_MAP.items():
        enums_dict[enum_name] = _get_enum_values(enum_class)
    
    return AllEnumsResponse(enums=enums_dict)


@router.get("/{enum_name}", response_model=EnumResponse)
async def get_enum_by_name(enum_name: str) -> EnumResponse:
    """Get a specific enum by name.
    
    Parameters
    ----------
    enum_name : str
        Name of the enum class (e.g., "OptionContentTypeEnum", "UserStatusEnum").
    
    Returns
    -------
    EnumResponse
        Enum with its name and list of values.
    
    Raises
    ------
    HTTPException
        404 if enum name is not found.
    """
    if enum_name not in ENUM_MAP:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enum '{enum_name}' not found. Available enums: {', '.join(ENUM_MAP.keys())}"
        )
    
    enum_class = ENUM_MAP[enum_name]
    values = _get_enum_values(enum_class)
    
    return EnumResponse(enum_name=enum_name, values=values)

