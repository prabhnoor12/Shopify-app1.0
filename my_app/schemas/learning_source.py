from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any


class LearningResource(BaseModel):
    id: int
    user_id: int
    source_type: str
    content: Optional[str] = None
    source_metadata: Optional[Dict[str, Any]] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class LearningResourceBase(BaseModel):
    source_type: str
    content: Optional[str] = None
    source_metadata: Optional[Dict[str, Any]] = None


class LearningResourceCreate(LearningResourceBase):
    pass


class LearningResourceUpdate(LearningResourceBase):
    pass


class LearningResourceRead(LearningResourceBase):
    id: int
    user_id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
