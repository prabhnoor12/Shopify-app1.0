"""
Consent model for GDPR compliance - granular consent management.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from .associations import Base


class Consent(Base):
    """User consent preferences for different data processing activities."""
    __tablename__ = "consents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("shopify_users.id"), nullable=False, index=True)

    # Consent categories
    necessary_cookies = Column(Boolean, default=True, nullable=False)  # Always required
    analytics_cookies = Column(Boolean, default=False, nullable=False)
    marketing_cookies = Column(Boolean, default=False, nullable=False)
    functional_cookies = Column(Boolean, default=False, nullable=False)

    # Data processing consents
    marketing_emails = Column(Boolean, default=False, nullable=False)
    product_updates = Column(Boolean, default=False, nullable=False)
    third_party_sharing = Column(Boolean, default=False, nullable=False)
    profiling = Column(Boolean, default=False, nullable=False)

    # Objections to processing (Right to Object under GDPR)
    object_marketing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Object to marketing
    object_profiling: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Object to profiling

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("ShopifyUser", back_populates="consents")

    def __repr__(self):
        return f"<Consent(user_id={self.user_id}, analytics={self.analytics_cookies}, marketing={self.marketing_cookies})>"
