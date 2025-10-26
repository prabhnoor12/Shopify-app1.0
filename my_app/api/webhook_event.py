"""
API routes for webhook event CRUD operations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db

from ..schemas.webhook import WebhookEventCreate, WebhookEventRead
from ..services.webhook_event_service import WebhookEventService
from ..models.webhook import WebhookEvent

router = APIRouter(prefix="/webhook-events", tags=["webhook-events"])


@router.post("/", response_model=WebhookEventRead)
def create_webhook_event(event: WebhookEventCreate, db: Session = Depends(get_db)):
    service = WebhookEventService(db)
    return service.create_webhook_event(event)


@router.get("/", response_model=List[WebhookEventRead])
def list_webhook_events(db: Session = Depends(get_db)):
    service = WebhookEventService(db)
    return service.db.query(WebhookEvent).all()


@router.get("/{event_id}", response_model=WebhookEventRead)
def get_webhook_event(event_id: int, db: Session = Depends(get_db)):
    service = WebhookEventService(db)
    event = service.get_webhook_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Webhook event not found.")
    return event


@router.delete("/{event_id}")
def delete_webhook_event(event_id: int, db: Session = Depends(get_db)):
    service = WebhookEventService(db)
    event = service.get_webhook_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Webhook event not found.")
    service.db.delete(event)
    service.db.commit()
    return {"detail": "Webhook event deleted."}
