from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime


class CalenderEventExtendedProps(BaseModel):
    """
    Holds extra data for a calender event, useful for the frontend.
    """

    status: str
    task_type: str
    payload: Dict[str, Any]
    error_message: Optional[str] = None
    recurrence_rule: Optional[str] = None


class CalenderEvent(BaseModel):
    """
    Represents a single event object for a calender frontend.
    """

    id: int
    title: str
    start: datetime
    end: datetime
    extendedProps: CalenderEventExtendedProps
    # You can add other properties like 'color' based on status
    color: Optional[str] = None


class CalenderEventCreate(BaseModel):
    """
    Schema for creating a new calender event.
    """

    title: str
    start: datetime
    end: datetime
    status: str
    task_type: str
    payload: Dict[str, Any]
    error_message: Optional[str] = None
    recurrence_rule: Optional[str] = None


class CalenderEventUpdate(BaseModel):
    """
    Schema for updating a calender event.
    """

    title: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    status: Optional[str] = None
    task_type: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    recurrence_rule: Optional[str] = None


class CalenderEventRead(BaseModel):
    """
    Schema for reading a calender event.
    """

    id: int
    title: str
    start: datetime
    end: datetime
    extendedProps: CalenderEventExtendedProps
    color: Optional[str] = None
