from pydantic import BaseModel, ConfigDict
from typing import Dict, Any


class PlanBase(BaseModel):
    name: str
    price: float
    features: Dict[str, Any]


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    features: Dict[str, Any] | None = None


class PlanRead(BaseModel):
    id: int
    name: str
    price: float
    features: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class Plan(PlanBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
