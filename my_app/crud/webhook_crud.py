from sqlalchemy.orm import Session
from my_app.models.webhook import Webhook


def get_webhook(db: Session, webhook_id: int):
    return db.query(Webhook).filter(Webhook.id == webhook_id).first()


def get_webhooks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Webhook).offset(skip).limit(limit).all()


def create_webhook(db: Session, webhook: dict):
    db_webhook = Webhook(**webhook)
    db.add(db_webhook)
    db.commit()
    db.refresh(db_webhook)
    return db_webhook


def update_webhook(db: Session, webhook_id: int, webhook_update: dict):
    db_webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if db_webhook:
        for key, value in webhook_update.items():
            setattr(db_webhook, key, value)
        db.commit()
        db.refresh(db_webhook)
    return db_webhook


def delete_webhook(db: Session, webhook_id: int):
    db_webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if db_webhook:
        db.delete(db_webhook)
        db.commit()
    return db_webhook
