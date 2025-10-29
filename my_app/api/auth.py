
import os
import logging
import secrets
import httpx
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from urllib.parse import urlparse, urlencode
from ..database import get_db
from ..utils.shopify import verify_shopify_hmac
from ..services.auth_service import AuthService
import asyncio


router = APIRouter(prefix="/auth")
logger = logging.getLogger(__name__)


SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET")
SHOPIFY_SCOPES = os.getenv("SHOPIFY_SCOPES")
APP_URL = os.getenv("APP_URL", "https://127.0.0.1:8000")


@router.get("/install")
async def install(shop: str, db: Session = Depends(get_db)) -> RedirectResponse:
    """
    Initiates Shopify OAuth installation flow using AuthService for nonce storage.
    """
    parsed_url = urlparse(shop)
    shop_domain = parsed_url.netloc or parsed_url.path
    if not shop_domain.endswith(".myshopify.com"):
        shop_domain += ".myshopify.com"
    redirect_uri = f"{APP_URL}/auth/callback"
    logger.info(f"OAuth redirect_uri being used: {redirect_uri}")
    nonce = secrets.token_urlsafe(16)
    auth_service = AuthService(db)
    await auth_service.store_nonce(shop_domain, nonce)
    auth_params = {
        "client_id": SHOPIFY_API_KEY,
        "scope": SHOPIFY_SCOPES,
        "redirect_uri": redirect_uri,
        "state": nonce,
    }
    auth_url = f"https://{shop_domain}/admin/oauth/authorize?{urlencode(auth_params)}"
    logger.info(f"Redirecting to Shopify OAuth for shop: {shop_domain}")
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    """
    Handles Shopify OAuth callback, exchanges code for access token, saves user/shop info, and validates nonce using AuthService.
    """
    query_params = dict(request.query_params)
    shop_domain = query_params.get("shop")
    code = query_params.get("code")
    state = query_params.get("state")
    if not shop_domain or not code or not state:
        logger.error("Missing shop, code, or state in callback.")
        raise HTTPException(
            status_code=400, detail="Missing shop, code, or state parameter."
        )
    auth_service = AuthService(db)
    # Validate nonce/state using AuthService (Redis)
    valid_nonce = await auth_service.validate_nonce(shop_domain, state)
    if not valid_nonce:
        logger.error(f"Invalid OAuth state for shop: {shop_domain}")
        raise HTTPException(status_code=401, detail="Invalid OAuth state.")
    if not verify_shopify_hmac(request):
        logger.error(f"HMAC verification failed for shop: {shop_domain}")
        raise HTTPException(status_code=403, detail="HMAC verification failed.")
    token_url = f"https://{shop_domain}/admin/oauth/access_token"
    payload = {
        "client_id": SHOPIFY_API_KEY,
        "client_secret": SHOPIFY_API_SECRET,
        "code": code,
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, json=payload)
            response.raise_for_status()
            data = response.json()
        # Shopify may return refresh_token in future, but for now only access_token is standard
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        if not access_token:
            logger.error(f"Failed to get access token for shop: {shop_domain}")
            raise HTTPException(status_code=400, detail="Failed to get access token.")
        # Use AuthService to handle OAuth callback and user creation/update
        user = auth_service.handle_oauth_callback(shop_domain, access_token, refresh_token=refresh_token)
        if not user:
            logger.error(f"Failed to create or update user for shop: {shop_domain}")
            raise HTTPException(status_code=500, detail="Failed to create or update user.")
        logger.info(f"OAuth successful for shop: {shop_domain}")
        # Redirect to frontend after successful authentication
        return RedirectResponse(url=f"https://shopify-app1-0.pages.dev/?shop={shop_domain}&access_token={access_token}")
    except httpx.RequestError as e:
        logger.error(f"OAuth token exchange failed for shop: {shop_domain}: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth token exchange failed: {e}")
