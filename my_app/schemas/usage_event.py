from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class UsageEventBase(BaseModel):
    user_id: int
    shop_id: int
    feature_name: str
    quantity: int = 1
    context: Optional[Dict[str, Any]] = None


class UsageEventCreate(UsageEventBase):
    pass


class UsageEventRead(UsageEventBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
