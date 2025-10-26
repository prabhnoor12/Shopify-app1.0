from pydantic import BaseModel, ConfigDict
from typing import List
from enum import Enum


class VariantBase(BaseModel):
    description: str


class VariantCreate(VariantBase):
    pass


class Variant(VariantBase):
    id: int
    impressions: int
    clicks: int
    conversions: int
    conversion_rate: float
    revenue: float
    ab_test_id: int
    model_config = ConfigDict(from_attributes=True)


class ABTestStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"
    CONCLUDED = "concluded"


class ABTestBase(BaseModel):
    product_id: int


class ABTestCreate(ABTestBase):
    variants: List[VariantCreate]


class ABTestUpdate(BaseModel):
    status: ABTestStatus
    variants: List[VariantCreate]


class ABTest(ABTestBase):
    id: int
    status: ABTestStatus
    variants: List[Variant] = []

    model_config = ConfigDict(from_attributes=True)
