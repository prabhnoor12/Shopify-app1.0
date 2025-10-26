from pydantic import BaseModel, ConfigDict
from typing import Optional
from enum import Enum


class FeedbackStatus(str, Enum):
    ACCEPTED = "accepted"
    EDITED = "edited"
    REJECTED = "rejected"


class UserFeedbackBase(BaseModel):
    """
    Base schema for user feedback.
    """

    original_text: str
    edited_text: Optional[str] = None
    status: FeedbackStatus


class UserFeedbackCreate(UserFeedbackBase):
    """
    Schema for creating user feedback.
    """

    pass


class UserFeedbackRead(UserFeedbackBase):
    """
    Schema for reading user feedback from the database.
    """

    id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)
