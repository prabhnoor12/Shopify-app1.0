from typing import Optional, List
from sqlalchemy.orm import Session
from .base import CRUDBase
from ..models.subscription import Subscription, SubscriptionStatus
from ..schemas.subscription import SubscriptionCreate, SubscriptionUpdate


class CRUDSubscription(CRUDBase[Subscription, SubscriptionCreate, SubscriptionUpdate]):
    def get_subscription_by_user(
        self, db: Session, *, user_id: int
    ) -> Optional[Subscription]:
        """
        Retrieves the most recent subscription for a given user, regardless of status.
        """
        return (
            db.query(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.id.desc())
            .first()
        )

    def get_active_subscription_by_user(
        self, db: Session, *, user_id: int
    ) -> Optional[Subscription]:
        """
        Retrieves the active subscription for a given user.
        """
        return (
            db.query(self.model)
            .filter(
                self.model.user_id == user_id,
                self.model.status == SubscriptionStatus.ACTIVE,
            )
            .first()
        )

    def get_by_shopify_subscription_id(
        self, db: Session, *, shopify_subscription_id: str
    ) -> Optional[Subscription]:
        """
        Retrieves a subscription by its Shopify subscription contract ID.
        """
        return (
            db.query(self.model)
            .filter(self.model.shopify_subscription_id == shopify_subscription_id)
            .first()
        )

    def get_all_by_user(self, db: Session, *, user_id: int) -> List[Subscription]:
        """
        Retrieves all subscriptions for a given user, ordered from newest to oldest.
        """
        return (
            db.query(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.id.desc())
            .all()
        )

    def get_by_status(
        self, db: Session, *, status: SubscriptionStatus
    ) -> List[Subscription]:
        """
        Retrieves all subscriptions with a specific status.
        """
        return db.query(self.model).filter(self.model.status == status).all()


subscription = CRUDSubscription(Subscription)
