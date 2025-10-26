from pydantic import BaseModel, ConfigDict
from typing import Optional
import datetime


class UsageBase(BaseModel):
    descriptions_generated_short: Optional[int] = 0
    descriptions_generated_long: Optional[int] = 0
    images_processed_sd: Optional[int] = 0
    images_processed_hd: Optional[int] = 0
    brand_voices_created: Optional[int] = 0
    brand_voice_edited: Optional[int] = 0
    analytics_reports_generated: Optional[int] = 0
    api_calls_made: Optional[int] = 0
    storage_used_mb: Optional[int] = 0


class UsageCreate(UsageBase):
    team_id: Optional[int] = None
    user_id: int


class UsageUpdate(UsageBase):
    pass


class Usage(UsageBase):
    id: int
    team_id: Optional[int] = None
    user_id: int
    timestamp: datetime.datetime
    last_activity_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class UsageEventCreate(BaseModel):
    user_id: int
    shop_id: int
    feature_name: str
    quantity: int
    context: Optional[dict] = None
    timestamp: Optional[datetime.datetime] = None


class UsageResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[dict] = None
    error: Optional[str] = None


class UsageRead(Usage):
    pass
