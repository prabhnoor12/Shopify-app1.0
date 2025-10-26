from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DB_ECHO: bool = os.getenv("DB_ECHO", "False").lower() == "true"
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", 5))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", 10))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", 30))

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_MAX_TOKENS: int = os.getenv("OPENAI_MAX_TOKENS", 150)
    OPENAI_TEMPERATURE: float = os.getenv("OPENAI_TEMPERATURE", 0.7)

    SHOPIFY_API_KEY: str = os.getenv("SHOPIFY_API_KEY", "")
    SHOPIFY_API_SECRET: str = os.getenv("SHOPIFY_API_SECRET", "")
    SHOPIFY_STORE_DOMAIN: str = os.getenv("SHOPIFY_STORE_DOMAIN", "")
    SHOPIFY_ADMIN_API_KEY: str = os.getenv("SHOPIFY_ADMIN_API_KEY", "")
    APP_URL: str = os.getenv("APP_URL", "http://127.0.0.1:8000")
    SHOPIFY_APP_RETURN_URL: str = os.getenv(
    "SHOPIFY_APP_RETURN_URL", "http://127.0.0.1:8000/shopify/auth/callback"
    )  # Default callback URL
    SHOPIFY_API_VERSION: str = os.getenv("SHOPIFY_API_VERSION", "2024-04")
    MONTHLY_GENERATION_LIMIT: int = os.getenv("MONTHLY_GENERATION_LIMIT", 100)
    REQUEST_TIMEOUT: int = os.getenv("REQUEST_TIMEOUT", 10)

    # --- SMTP Settings for Email Notifications ---
    SMTP_SERVER: str = os.getenv(
        "SMTP_SERVER",
    )
    SMTP_PORT: int = os.getenv(
        "SMTP_PORT",
    )
    SMTP_USER: str = os.getenv(
        "SMTP_USER",
    )
    SMTP_PASSWORD: str = os.getenv(
        "SMTP_PASSWORD",
    )
    SMTP_SENDER_NAME: str = os.getenv(
        "SMTP_SENDER_NAME",
    )

    SHOPIFY_WEBHOOK_SECRET: str = os.getenv("SHOPIFY_WEBHOOK_SECRET", "")
    SHOPIFY_APP_NAME: str = os.getenv(
        "SHOPIFY_APP_NAME", "my-shopify-app"
    )  # Default app name
    SHOPIFY_BILLING_TEST_MODE: bool = (
        os.getenv("SHOPIFY_BILLING_TEST_MODE", "True").lower() == "true"
    )  # Default to True for testing

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()


@lru_cache()
def get_settings():
    return settings
