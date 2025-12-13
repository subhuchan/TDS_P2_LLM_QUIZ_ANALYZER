"""Data models and validation for the LLM Analysis Quiz System."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator


class AnswerFormat(str, Enum):
    """Supported answer formats for quiz responses."""
    
    BOOLEAN = "boolean"
    NUMBER = "number"
    STRING = "string"
    BASE64 = "base64"
    JSON = "json"


class QuizRequest(BaseModel):
    """Request model for incoming quiz tasks."""
    
    email: EmailStr = Field(..., description="Student email address")
    secret: str = Field(..., min_length=1, description="Authentication secret string")
    url: HttpUrl = Field(..., description="Quiz URL to solve")
    
    @field_validator("secret")
    @classmethod
    def validate_secret(cls, v: str) -> str:
        """Validate that secret is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError("Secret cannot be empty or whitespace only")
        return v.strip()


class QuizResponse(BaseModel):
    """Response model for quiz request acknowledgment."""
    
    status: str = Field(..., description="Response status")
    message: Optional[str] = Field(None, description="Optional message")


class TaskDefinition(BaseModel):
    """Parsed task definition from quiz page."""
    
    instructions: str = Field(..., description="Decoded task instructions")
    submit_url: HttpUrl = Field(..., description="Endpoint URL for answer submission")
    answer_format: AnswerFormat = Field(..., description="Required answer format")
    file_urls: List[HttpUrl] = Field(default_factory=list, description="URLs of files to download")
    additional_context: Dict[str, Any] = Field(default_factory=dict, description="Additional task context")


class SubmitPayload(BaseModel):
    """Payload for submitting answers to quiz endpoint."""
    
    email: EmailStr = Field(..., description="Student email address")
    secret: str = Field(..., min_length=1, description="Authentication secret string")
    url: HttpUrl = Field(..., description="Original quiz URL")
    answer: Any = Field(..., description="Computed answer in required format")
    
    @field_validator("secret")
    @classmethod
    def validate_secret(cls, v: str) -> str:
        """Validate that secret is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError("Secret cannot be empty or whitespace only")
        return v.strip()


class SubmitResponse(BaseModel):
    """Response from answer submission endpoint."""
    
    correct: bool = Field(..., description="Whether the answer was correct")
    reason: Optional[str] = Field(None, description="Explanation if answer was incorrect")
    url: Optional[HttpUrl] = Field(None, description="Next quiz URL if available")


class QuizResult(BaseModel):
    """Final result of quiz solving sequence."""
    
    success: bool = Field(..., description="Whether quiz sequence completed successfully")
    total_time: float = Field(..., ge=0, description="Total time taken in seconds")
    quizzes_solved: int = Field(..., ge=0, description="Number of quizzes solved")
    final_status: str = Field(..., description="Final status message")
    error: Optional[str] = Field(None, description="Error message if failed")
