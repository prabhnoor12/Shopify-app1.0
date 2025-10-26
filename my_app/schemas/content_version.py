"""
Pydantic schemas for ContentVersion.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ContentVersionBase(BaseModel):
    title: str
    body_html: Optional[str] = None
    reason_for_change: Optional[str] = None


class ContentVersionCreate(ContentVersionBase):
    product_id: int
    version: int
    updated_by_id: int


class ContentVersion(ContentVersionBase):
    id: int
    product_id: int
    version: int
    created_at: datetime
    updated_by_id: int

    class Config:
        from_attributes = True
