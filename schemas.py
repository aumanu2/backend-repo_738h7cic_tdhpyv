"""
Database Schemas for Coding Platform

Each Pydantic model corresponds to a MongoDB collection.
Collection name is the lowercase of the class name.

Collections:
- User -> "user"
- Test -> "test"
- Attempt -> "attempt"
- Submission -> "submission"
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

Role = Literal["test_taker", "manager", "admin"]
QuestionType = Literal["mcq", "code"]


class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    role: Role = Field("test_taker")
    avatar_url: Optional[str] = None
    is_active: bool = True


class Option(BaseModel):
    id: str = Field(..., description="Client-side id for the option (e.g., 'A','B')")
    text: str
    correct: bool = False


class Question(BaseModel):
    title: str
    type: QuestionType = "mcq"
    prompt: str
    options: Optional[List[Option]] = None
    points: int = 1
    starter_code: Optional[str] = None
    language: Optional[str] = Field(None, description="e.g. 'python','javascript'")


class Test(BaseModel):
    title: str
    description: str
    duration_minutes: int = 60
    tags: List[str] = []
    published: bool = False
    questions: List[Question] = []
    created_by: Optional[str] = Field(None, description="creator email")


class Submission(BaseModel):
    attempt_id: str
    test_id: str
    question_index: int
    answer_option_ids: Optional[List[str]] = None
    code_answer: Optional[str] = None
    language: Optional[str] = None
    created_at: Optional[datetime] = None


class Attempt(BaseModel):
    test_id: str
    user_email: str
    user_name: str
    status: Literal["active", "finished"] = "active"
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    score: Optional[float] = 0
    total_points: Optional[int] = 0
    submissions: List[str] = []  # store submission ids
