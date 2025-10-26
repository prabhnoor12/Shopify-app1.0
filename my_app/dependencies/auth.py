"""
Authentication dependencies for FastAPI routes.
"""

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.auth_service import AuthService
from my_app.utils.shopify import is_valid_shop_domain
from my_app.utils.security import timing_safe_compare


def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    Dependency to get the current authenticated Shopify user based on a token in headers or cookies.
    Utilizes utility functions for shop domain validation and timing-safe token comparison.
    """
    shop_domain = request.headers.get("X-Shop-Domain")
    access_token = request.headers.get("X-Shop-Token")
    if not shop_domain or not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication headers.",
        )
    if not is_valid_shop_domain(shop_domain):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid shop domain format.",
        )
    auth_service = AuthService(db)
    user = auth_service.get_user(shop_domain)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    # Use timing-safe compare for token validation
    if not timing_safe_compare(user.access_token, access_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token."
        )
    return user
