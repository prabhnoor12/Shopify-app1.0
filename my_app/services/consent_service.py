"""
Service for managing user consent preferences for GDPR compliance.
"""

from sqlalchemy.orm import Session
from ..models.consent import Consent
from ..models.shop import ShopifyUser
from typing import Optional, Dict
import json


class ConsentService:
    """
    Provides business logic for managing user consent preferences.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_user_consent(self, user_id: int) -> Optional[Consent]:
        """Get consent preferences for a user."""
        return self.db.query(Consent).filter(Consent.user_id == user_id).first()

    def create_or_update_consent(
        self,
        user_id: int,
        consent_data: Dict[str, bool],
        ip_address: str = None,
        user_agent: str = None
    ) -> Consent:
        """Create or update user consent preferences."""
        consent = self.get_user_consent(user_id)

        if consent:
            # Update existing consent
            for key, value in consent_data.items():
                if hasattr(consent, key):
                    setattr(consent, key, value)
            if ip_address:
                consent.ip_address = ip_address
            if user_agent:
                consent.user_agent = user_agent
        else:
            # Create new consent
            consent = Consent(
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                **consent_data
            )
            self.db.add(consent)

        self.db.commit()
        self.db.refresh(consent)
        return consent

    def withdraw_consent(self, user_id: int, consent_type: str) -> bool:
        """Withdraw specific consent type for a user."""
        consent = self.get_user_consent(user_id)
        if not consent:
            return False

        # Define which fields can be withdrawn
        withdrawable_fields = {
            "analytics_cookies": False,
            "marketing_cookies": False,
            "functional_cookies": False,
            "marketing_emails": False,
            "product_updates": False,
            "third_party_sharing": False,
            "profiling": False,
        }

        if consent_type not in withdrawable_fields:
            return False

        setattr(consent, consent_type, False)
        self.db.commit()
        return True

    def has_consent(self, user_id: int, consent_type: str) -> bool:
        """Check if user has given consent for a specific type."""
        consent = self.get_user_consent(user_id)
        if not consent:
            # Default to False for most consents, True for necessary
            return consent_type == "necessary_cookies"

        return getattr(consent, consent_type, False)

    def get_consent_summary(self, user_id: int) -> Dict[str, bool]:
        """Get a summary of all consent preferences for a user."""
        consent = self.get_user_consent(user_id)
        if not consent:
            # Return defaults
            return {
                "necessary_cookies": True,
                "analytics_cookies": False,
                "marketing_cookies": False,
                "functional_cookies": False,
                "marketing_emails": False,
                "product_updates": False,
                "third_party_sharing": False,
                "profiling": False,
            }

    def object_to_processing(self, user_id: int, objection_type: str) -> bool:
        """Allow user to object to specific data processing activities."""
        consent = self.get_user_consent(user_id)
        if not consent:
            return False

        objection_fields = {
            "marketing": "object_marketing",
            "profiling": "object_profiling",
        }

        if objection_type not in objection_fields:
            return False

        field_name = objection_fields[objection_type]
        setattr(consent, field_name, True)
        self.db.commit()
        return True

    def has_objection(self, user_id: int, objection_type: str) -> bool:
        """Check if user has objected to specific processing."""
        consent = self.get_user_consent(user_id)
        if not consent:
            return False

        objection_fields = {
            "marketing": "object_marketing",
            "profiling": "object_profiling",
        }

        if objection_type not in objection_fields:
            return False

        return getattr(consent, objection_fields[objection_type], False)
