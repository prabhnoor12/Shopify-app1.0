"""
Centralized configuration settings for the application.
"""

import os
from pydantic_settings import BaseSettings


class ShopifySettings(BaseSettings):
    api_key: str = os.getenv("SHOPIFY_API_KEY", "")
    api_secret: str = os.getenv("SHOPIFY_API_SECRET", "")
    app_url: str = os.getenv("SHOPIFY_APP_URL", "")
    webhook_secret: str = os.getenv("SHOPIFY_WEBHOOK_SECRET", "")


class AppSettings(BaseSettings):
    shopify: ShopifySettings = ShopifySettings()
    secret_key: str = os.getenv("SECRET_KEY", "your-default-secret")


settings = AppSettings()
