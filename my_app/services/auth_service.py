"""
Service for handling Shopify OAuth and authentication logic.
Enhanced for robustness, logging, audit, and token management.
"""

import logging
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from ..crud.shop_crud import (
    create_or_update_user,
    get_user_by_domain,
    revoke_user_token,
)
from ..models.shop import ShopifyUser
from my_app.utils.shopify import format_shop_domain

logger = logging.getLogger(__name__)


class AuthService:
    def install_shop(self, shop_domain: str, access_token: str, plan: str = "free", install_metadata: Optional[dict] = None) -> Optional[ShopifyUser]:
        """
        Handle new shop install: create shop record, store metadata, trigger onboarding, and audit.
        """
        try:
            normalized_domain = format_shop_domain(shop_domain)
            metadata = install_metadata or {}
            user = create_or_update_user(
                self.db,
                normalized_domain,
                access_token,
                plan=plan,
                install_date=datetime.utcnow(),
                metadata=metadata,
            )
            logger.info(f"Shop installed: {normalized_domain} | plan={plan}")
            self._audit_event("shop_installed", normalized_domain, success=True)
            self._metric_event("shop_installed", normalized_domain, success=True)
            self._trigger_onboarding(normalized_domain)
            return user
        except Exception as e:
            logger.error(f"Shop install failed for {shop_domain}: {e}")
            self._audit_event("shop_installed", shop_domain, success=False, error=str(e))
            self._metric_event("shop_installed", shop_domain, success=False)
            return None

    def uninstall_shop(self, shop_domain: str) -> bool:
        """
        Handle shop uninstall: deactivate user, revoke tokens, cleanup, and audit.
        """
        try:
            normalized_domain = format_shop_domain(shop_domain)
            user = get_user_by_domain(self.db, normalized_domain)
            if not user:
                logger.warning(f"Uninstall: user not found for {shop_domain}")
                return False
            user.is_active = False
            user.uninstall_date = datetime.utcnow()
            user.access_token = None
            user.refresh_token = None
            self.db.commit()
            logger.info(f"Shop uninstalled: {normalized_domain}")
            self._audit_event("shop_uninstalled", normalized_domain, success=True)
            self._metric_event("shop_uninstalled", normalized_domain, success=True)
            self._cleanup_shop_data(normalized_domain)
            return True
        except Exception as e:
            logger.error(f"Shop uninstall failed for {shop_domain}: {e}")
            self._audit_event("shop_uninstalled", shop_domain, success=False, error=str(e))
            self._metric_event("shop_uninstalled", shop_domain, success=False)
            return False

    def _trigger_onboarding(self, shop_domain: str) -> None:
        """
        Placeholder for onboarding logic (e.g., send welcome email, setup defaults).
        """
        # TODO: Implement onboarding workflow
        logger.info(f"Onboarding triggered for shop {shop_domain}")

    def _cleanup_shop_data(self, shop_domain: str) -> None:
        """
        Placeholder for shop data cleanup logic (e.g., remove data, cancel jobs).
        """
        # TODO: Implement cleanup workflow
        logger.info(f"Cleanup triggered for shop {shop_domain}")
    """
    Handles Shopify OAuth, authentication, token management, audit, and state/nonce logic.
    """

    def __init__(self, db: Session):
        self.db = db

    def handle_oauth_callback(
        self, shop_domain: str, access_token: str, refresh_token: Optional[str] = None
    ) -> Optional[ShopifyUser]:
        """
        Create or update a Shopify user after OAuth callback. Logs and audits the event.
        Supports refresh token and last login tracking.
        """
        try:
            normalized_domain = format_shop_domain(shop_domain)
            user = create_or_update_user(
                self.db, normalized_domain, access_token, refresh_token=refresh_token
            )
            self._track_last_login(normalized_domain)
            logger.info(f"OAuth callback handled for shop: {normalized_domain}")
            self._audit_event("oauth_callback", normalized_domain, success=True)
            self._metric_event("oauth_callback", normalized_domain, success=True)
            return user
        except Exception as e:
            logger.error(f"OAuth callback failed for shop: {shop_domain}: {e}")
            self._audit_event(
                "oauth_callback", shop_domain, success=False, error=str(e)
            )
            self._metric_event("oauth_callback", shop_domain, success=False)
            return None
    def refresh_access_token(self, shop_domain: str) -> Optional[str]:
        """
        Refresh the access token for a shop if a refresh token is available.
        """
        try:
            user = get_user_by_domain(self.db, format_shop_domain(shop_domain))
            if not user or not getattr(user, "refresh_token", None):
                logger.warning(f"No refresh token for shop {shop_domain}")
                return None
            # Placeholder: Call Shopify or your OAuth provider to refresh
            new_token = self._external_refresh_token(user.refresh_token)
            user.access_token = new_token
            self.db.commit()
            logger.info(f"Refreshed access token for shop {shop_domain}")
            self._audit_event("token_refreshed", shop_domain, success=True)
            self._metric_event("token_refreshed", shop_domain, success=True)
            return new_token
        except Exception as e:
            logger.error(f"Token refresh failed for shop {shop_domain}: {e}")
            self._audit_event("token_refreshed", shop_domain, success=False, error=str(e))
            self._metric_event("token_refreshed", shop_domain, success=False)
            return None

    def deactivate_user(self, shop_domain: str) -> bool:
        """
        Deactivate a user/shop (e.g., on uninstall or abuse). Logs and audits.
        """
        try:
            user = get_user_by_domain(self.db, format_shop_domain(shop_domain))
            if not user:
                logger.warning(f"Deactivate: user not found for {shop_domain}")
                return False
            user.is_active = False
            self.db.commit()
            logger.info(f"Deactivated user for shop {shop_domain}")
            self._audit_event("user_deactivated", shop_domain, success=True)
            self._metric_event("user_deactivated", shop_domain, success=True)
            return True
        except Exception as e:
            logger.error(f"User deactivation failed for shop {shop_domain}: {e}")
            self._audit_event("user_deactivated", shop_domain, success=False, error=str(e))
            self._metric_event("user_deactivated", shop_domain, success=False)
            return False

    def _track_last_login(self, shop_domain: str) -> None:
        """
        Update last_login timestamp for a shop/user.
        """
        try:
            user = get_user_by_domain(self.db, format_shop_domain(shop_domain))
            if user:
                user.last_login = datetime.utcnow()
                self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to update last_login for {shop_domain}: {e}")

    def _external_refresh_token(self, refresh_token: str) -> str:
        """
        Placeholder for external refresh token logic (call Shopify or OAuth provider).
        """
        # TODO: Implement actual refresh logic
        return refresh_token + "_new"

    def _metric_event(self, event_type: str, shop_domain: str, success: bool) -> None:
        """
        Placeholder for metrics hook (e.g., Prometheus, StatsD).
        """
        # TODO: Integrate with metrics system
        pass

    def validate_access_token(self, shop_domain: str, token: str) -> bool:
        """
        Validate if the provided access token matches the stored one for the shop. Logs result.
        Also checks if user is active.
        """
        try:
            user = get_user_by_domain(self.db, format_shop_domain(shop_domain))
            valid = (
                user is not None and user.access_token == token and getattr(user, "is_active", True)
            )
            logger.info(f"Access token validation for shop {shop_domain}: {valid}")
            self._metric_event("access_token_validated", shop_domain, success=valid)
            return valid
        except Exception as e:
            logger.error(f"Access token validation error for shop {shop_domain}: {e}")
            self._metric_event("access_token_validated", shop_domain, success=False)
            return False

    def get_user(self, shop_domain: str) -> Optional[ShopifyUser]:
        """
        Retrieve a user by shop domain. Logs lookup.
        """
        try:
            user = get_user_by_domain(self.db, format_shop_domain(shop_domain))
            logger.info(
                f"User lookup for shop {shop_domain}: {'found' if user else 'not found'}"
            )
            return user
        except Exception as e:
            logger.error(f"User lookup error for shop {shop_domain}: {e}")
            return None

    def revoke_token(self, shop_domain: str) -> bool:
        """
        Revoke a user's access token (logout/shop uninstall). Logs and audits the event.
        """
        try:
            normalized_domain = format_shop_domain(shop_domain)
            success = revoke_user_token(self.db, normalized_domain)
            logger.info(f"Token revoked for shop: {normalized_domain}")
            self._audit_event("token_revoked", normalized_domain, success=success)
            return success
        except Exception as e:
            logger.error(f"Token revocation failed for shop: {shop_domain}: {e}")
            self._audit_event("token_revoked", shop_domain, success=False, error=str(e))
            return False

    def _audit_event(
        self,
        event_type: str,
        shop_domain: str,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """
        Internal: Record an audit event for authentication actions in the database.
        """
        try:
            from my_app.models.audit import AuditLog

            audit = AuditLog(
                event_type=event_type,
                shop_domain=shop_domain,
                success=success,
                error=error,
                timestamp=datetime.utcnow(),
            )
            self.db.add(audit)
            self.db.commit()
            logger.info(
                f"AUDIT: {event_type} for {shop_domain} | success={success} | error={error}"
            )
        except Exception as e:
            logger.error(f"Failed to persist audit event: {e}")

    async def store_nonce(self, shop_domain: str, nonce: str) -> None:
        """
        Store OAuth nonce/state for a shop in Redis (for CSRF protection).
        """
        from my_app.dependencies.redis import get_redis_client

        redis_client = get_redis_client()
        key = f"shopify:nonce:{shop_domain}"
        await redis_client.set(key, nonce, ex=600)  # 10 min expiry
        logger.debug(f"Stored nonce for shop {shop_domain}: {nonce}")

    async def validate_nonce(self, shop_domain: str, nonce: str) -> bool:
        """
        Validate OAuth nonce/state for a shop using Redis.
        """
        from my_app.dependencies.redis import get_redis_client

        redis_client = get_redis_client()
        key = f"shopify:nonce:{shop_domain}"
        stored_nonce = await redis_client.get(key)
        valid = stored_nonce == nonce
        logger.debug(
            f"Validating nonce for shop {shop_domain}: {nonce} | valid={valid}"
        )
        if valid:
            await redis_client.delete(key)
        return valid

