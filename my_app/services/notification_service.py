import os
from typing import List, Optional, Tuple
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from twilio.rest import Client as TwilioClient
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential
from .. import crud
from ..schemas.notification import EventType, NotificationCreate
from ..schemas.notification import Notification as NotificationSchema
from ..crud.user_notification_preference_crud import get_user_notification_preference

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
FROM_EMAIL = os.getenv("FROM_EMAIL")


class NotificationService:
    """
    This service handles all user notifications, both event-driven and behavior-driven.

    Event-Driven Notifications:
    - PRODUCT_LIVE: Sent when a user's product is published and becomes available on their Shopify store.
    - SCHEDULED_PRODUCT_READY: Sent when a set of products scheduled for future publication are ready for the user's review and approval.
    - SUBSCRIPTION_UPDATE: Sent when a user's subscription plan is successfully updated (e.g., upgrade or downgrade).
    - SYSTEM_ALERT: Sent to all users to notify them about important system-wide updates, maintenance, or issues.
    - NEW_FEATURE_ANNOUNCEMENT: Sent to announce a new feature or functionality in the application.
    - TRIAL_EXPIRING_SOON: Sent to users on a trial plan a few days before their trial period ends.
    - PAYMENT_FAILED: Sent when a user's subscription payment fails.

    Behavior-Driven Notifications:
    - USER_INACTIVITY: Sent to a user who has not logged in for a specific period (e.g., 7 days) to encourage them to re-engage with the application.
    - CONTENT_CALENDAR_EMPTY: Sent when a user's content calendar for the upcoming week is empty, prompting them to schedule new content.
    - AB_TEST_COMPLETED: Sent when an A/B test for a product has concluded, prompting the user to review the results.
    - UNREAD_NOTIFICATIONS: Sent as a digest to users who have unread notifications in the application.
    - FEATURE_NOT_USED: Sent to users who have not used a specific key feature of the application after a certain period, encouraging them to try it out.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_notification_content(
        self, event_type: EventType, data: dict, channel: str
    ) -> Tuple[str, str]:
        subject = "Notification"
        message = "You have a new notification."

        if event_type == EventType.PRODUCT_LIVE:
            product_name = data.get("product_name", "N/A")
            subject = f"Product Live: {product_name}"
            if channel == "email":
                message = (
                    f"<p>Your product <strong>{product_name}</strong> is now live!</p>"
                )
            else:
                message = f"Your product {product_name} is now live!"

        elif event_type == EventType.SCHEDULED_PRODUCT_READY:
            subject = "Scheduled Products Ready"
            if channel == "email":
                message = "<p>Your scheduled products are ready to go live. Please review and approve them in your dashboard.</p>"
            else:
                message = (
                    "Your scheduled products are ready. Please review and approve."
                )

        elif event_type == EventType.USER_INACTIVITY:
            subject = "We Miss You!"
            if channel == "email":
                message = "<p>Your content calendar is looking empty. Let us help you generate some fresh ideas!</p>"
            else:
                message = "Your content calendar is empty. Let us help!"

        elif event_type == EventType.SUBSCRIPTION_UPDATE:
            plan_name = data.get("plan_name", "N/A")
            subject = "Subscription Updated"
            if channel == "email":
                message = f"<p>Your subscription has been successfully updated to the <strong>{plan_name}</strong> plan.</p>"
            else:
                message = f"Your subscription is now {plan_name}."

        elif event_type == EventType.SYSTEM_ALERT:
            alert_message = data.get("alert_message", "Important system update.")
            subject = "System Alert"
            if channel == "email":
                message = f"<p><strong>System Alert:</strong> {alert_message}</p>"
            else:
                message = f"System Alert: {alert_message}"

        return subject, message

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def send_email(
        self, to_email: str, subject: str, message: str, template: Optional[str] = None
    ) -> bool:
        if not SENDGRID_API_KEY or not FROM_EMAIL:
            raise RuntimeError("SendGrid API key or FROM_EMAIL not set in environment.")
        try:
            mail = Mail(
                from_email=FROM_EMAIL,
                to_emails=to_email,
                subject=subject,
                html_content=template if template else message,
            )
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(mail)
            return response.status_code in (200, 202)
        except Exception as e:
            print(f"SendGrid error: {e}")
            return False

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def send_sms(self, to_number: str, message: str) -> bool:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_FROM_NUMBER:
            raise RuntimeError("Twilio credentials not set in environment.")
        try:
            client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            msg = client.messages.create(
                body=message, from_=TWILIO_FROM_NUMBER, to=to_number
            )
            return msg.sid is not None
        except Exception as e:
            print(f"Twilio error: {e}")
            return False

    def send_invitation_email(self, to_email: str, invitation_link: str):
        subject = "You have been invited to join a team"
        message = f"Click the link to accept the invitation: {invitation_link}"
        self.send_email(to_email, subject, message)

    def notify_event(self, user_id: int, event_type: EventType, data: dict) -> None:
        crud.notification.create_notification(
            self.db,
            NotificationCreate(user_id=user_id, event_type=event_type, data=data),
        )
        user = crud.user.get_user(self.db, user_id=user_id)
        if not user:
            return

        preferences = get_user_notification_preference(self.db, user_id=user_id)

        if preferences and preferences.email_enabled and user.email:
            subject, message = self._get_notification_content(event_type, data, "email")
            self.send_email(user.email, subject, message)

        if preferences and preferences.sms_enabled and user.phone_number:
            _, message = self._get_notification_content(event_type, data, "sms")
            self.send_sms(user.phone_number, message)

    def bulk_notify(
        self, user_ids: List[int], event_type: EventType, data: dict
    ) -> None:
        for user_id in user_ids:
            self.notify_event(user_id, event_type, data)

    def get_notifications(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[NotificationSchema]:
        return crud.notification.get_notifications_by_user(
            self.db, user_id=user_id, skip=skip, limit=limit
        )

    def mark_notification_as_read(
        self, notification_id: int
    ) -> Optional[NotificationSchema]:
        return crud.notification.mark_notification_as_read(
            self.db, notification_id=notification_id
        )
