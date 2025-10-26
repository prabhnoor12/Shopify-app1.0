
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from my_app.services.auth_service import AuthService
from my_app.models.shop import ShopifyUser

@pytest.fixture
def db():
    db = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.add = MagicMock()
    return db

@pytest.mark.asyncio
async def test_store_and_validate_nonce(db):
    service = AuthService(db)
    shop_domain = "testshop.myshopify.com"
    nonce = "abc123"
    with patch("my_app.dependencies.redis.get_redis_client") as mock_redis:
        redis = AsyncMock()
        mock_redis.return_value = redis
        await service.store_nonce(shop_domain, nonce)
        redis.set.assert_awaited_with(f"shopify:nonce:{shop_domain}", nonce, ex=600)
        redis.get.return_value = nonce
        valid = await service.validate_nonce(shop_domain, nonce)
        assert valid
        redis.delete.assert_awaited_with(f"shopify:nonce:{shop_domain}")

def test_install_shop_success(db):
    service = AuthService(db)
    shop_domain = "testshop.myshopify.com"
    access_token = "token"
    with patch("my_app.services.auth_service.create_or_update_user", new=MagicMock(return_value=ShopifyUser(shop_domain=shop_domain, access_token=access_token))):
        with patch.object(service, '_audit_event'), patch.object(service, '_metric_event'), patch.object(service, '_trigger_onboarding'):
            user = service.install_shop(shop_domain, access_token)
            assert user.shop_domain == shop_domain

def test_handle_oauth_callback_success(db):
    service = AuthService(db)
    shop_domain = "testshop.myshopify.com"
    access_token = "token"
    with patch("my_app.services.auth_service.create_or_update_user", new=MagicMock(return_value=ShopifyUser(shop_domain=shop_domain, access_token=access_token))):
        with patch.object(service, '_audit_event'), patch.object(service, '_metric_event'), patch.object(service, '_track_last_login'):
            user = service.handle_oauth_callback(shop_domain, access_token)
            assert user.shop_domain == shop_domain

def test_deactivate_user(db):
    service = AuthService(db)
    shop_domain = "testshop.myshopify.com"
    user = ShopifyUser(shop_domain=shop_domain, access_token="token", is_active=True)
    with patch("my_app.services.auth_service.get_user_by_domain", new=MagicMock(return_value=user)):
        with patch.object(service, '_audit_event'), patch.object(service, '_metric_event'):
            result = service.deactivate_user(shop_domain)
            assert result is True

def test_get_user(db):
    service = AuthService(db)
    shop_domain = "testshop.myshopify.com"
    user = ShopifyUser(shop_domain=shop_domain, access_token="token")
    with patch("my_app.services.auth_service.get_user_by_domain", new=MagicMock(return_value=user)):
        result = service.get_user(shop_domain)
        assert result == user
