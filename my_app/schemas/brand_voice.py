from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class BrandVoiceBase(BaseModel):
    tone_of_voice: Optional[str] = None
    vocabulary_preferences: Optional[dict] = None
    industry_jargon: Optional[List[str]] = None
    banned_words: Optional[List[str]] = None
    description: Optional[str] = None


class BrandVoiceCreate(BrandVoiceBase):
    pass


class BrandVoiceUpdate(BrandVoiceBase):
    pass


class BrandVoiceRead(BrandVoiceBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)
