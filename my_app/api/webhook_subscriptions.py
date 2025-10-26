from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas.webhook import WebhookEventCreate, WebhookEventRead, WebhookEventUpdate
from ..crud import webhook_crud

router = APIRouter(prefix="/webhook-subscriptions", tags=["webhook-subscriptions"])


@router.post("/", response_model=WebhookEventRead)
def create_webhook_subscription(
    webhook: WebhookEventCreate, db: Session = Depends(get_db)
):
    return webhook_crud.create_webhook(db=db, webhook=webhook.dict())


@router.get("/", response_model=List[WebhookEventRead])
def list_webhook_subscriptions(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return webhook_crud.get_webhooks(db=db, skip=skip, limit=limit)


@router.get("/{webhook_id}", response_model=WebhookEventRead)
def get_webhook_subscription(webhook_id: int, db: Session = Depends(get_db)):
    webhook = webhook_crud.get_webhook(db=db, webhook_id=webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook subscription not found.")
    return webhook


@router.put("/{webhook_id}", response_model=WebhookEventRead)
def update_webhook_subscription(
    webhook_id: int, webhook_update: WebhookEventUpdate, db: Session = Depends(get_db)
):
    webhook = webhook_crud.update_webhook(
        db=db,
        webhook_id=webhook_id,
        webhook_update=webhook_update.dict(exclude_unset=True),
    )
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook subscription not found.")
    return webhook


@router.delete("/{webhook_id}")
def delete_webhook_subscription(webhook_id: int, db: Session = Depends(get_db)):
    webhook = webhook_crud.delete_webhook(db=db, webhook_id=webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook subscription not found.")
    return {"detail": "Webhook subscription deleted"}
