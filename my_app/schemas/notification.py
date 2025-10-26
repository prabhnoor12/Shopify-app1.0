from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from .user import User
from enum import Enum


class EventType(str, Enum):
    # A/B Testing Events
    AB_TEST_CREATED = "ab_test_created"
    AB_TEST_COMPLETED = "ab_test_completed"
    AB_TEST_WINNER_PROMOTED = "ab_test_winner_promoted"

    # Approval Workflow Events
    APPROVAL_REQUEST_CREATED = "approval_request_created"
    APPROVAL_STATUS_CHANGED = "approval_status_changed"

    # Agency & Team Events
    AGENCY_MEMBER_ADDED = "agency_member_added"
    CLIENT_ADDED_TO_AGENCY = "client_added_to_agency"

    # Content & Product Events
    CONTENT_GENERATED = "content_generated"
    PRODUCT_LIVE = "product_live"
    SCHEDULED_PRODUCT_READY = "scheduled_product_ready"

    # User & System Events
    USER_INACTIVITY = "user_inactivity"
    SUBSCRIPTION_UPDATE = "subscription_update"
    SYSTEM_ALERT = "system_alert"


class NotificationBase(BaseModel):
    event_type: EventType
    data: Optional[Dict[str, Any]] = None


class NotificationCreate(NotificationBase):
    user_id: int


class NotificationUpdate(NotificationBase):
    is_read: Optional[bool] = None
    data: Optional[Dict[str, Any]] = None


class Notification(NotificationBase):
    id: int
    user: User
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
