"""
Service for webhook event deduplication and processing.
"""

from sqlalchemy.orm import Session
from ..models.webhook import WebhookEvent
from ..schemas.webhook import WebhookEventCreate


class WebhookEventService:
    def __init__(self, db: Session):
        self.db = db

    def create_webhook_event(self, event: WebhookEventCreate) -> WebhookEvent:
        db_event = WebhookEvent(**event.dict())
        self.db.add(db_event)
        self.db.commit()
        self.db.refresh(db_event)
        return db_event

    def get_webhook_event(self, event_id: int) -> WebhookEvent:
        return self.db.query(WebhookEvent).get(event_id)

    def list_webhook_events(
        self, skip: int = 0, limit: int = 100
    ) -> list[WebhookEvent]:
        return self.db.query(WebhookEvent).offset(skip).limit(limit).all()

    def delete_webhook_event(self, event_id: int) -> WebhookEvent:
        event = self.get_webhook_event(event_id)
        if event:
            self.db.delete(event)
            self.db.commit()
        return event
