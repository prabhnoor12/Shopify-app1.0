from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from ..services.notification_service import NotificationService
from ..database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/notifications", tags=["notifications"])


class EmailNotification(BaseModel):
    to_email: str
    subject: str
    message: str
    template: Optional[str] = None


class SmsNotification(BaseModel):
    to_number: str
    message: str


@router.post("/send-email")
async def send_email(
    notification: EmailNotification, db: AsyncSession = Depends(get_db)
):
    """
    Send an email notification to a user.
    """
    notification_service = NotificationService(db)
    success = await notification_service.send_email(
        to_email=notification.to_email,
        subject=notification.subject,
        message=notification.message,
        template=notification.template,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email")
    return {"message": "Email sent successfully"}


@router.post("/send-sms")
async def send_sms(notification: SmsNotification, db: AsyncSession = Depends(get_db)):
    """
    Send an SMS notification to a user.
    """
    notification_service = NotificationService(db)
    success = await notification_service.send_sms(
        to_number=notification.to_number,
        message=notification.message,
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send SMS")
    return {"message": "SMS sent successfully"}
