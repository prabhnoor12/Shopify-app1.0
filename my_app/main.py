
from fastapi.responses import JSONResponse

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from .middleware.cors import add_cors_middleware
from .middleware.logging import add_logging_middleware
from .middleware.error_handler import add_exception_handlers
from .middleware.rate_limiting import RateLimitingMiddleware
from .middleware.auth import AuthMiddleware
from .middleware.request_validation import RequestValidationMiddleware


from .api.shopify_openai import router as shopify_openai_router
from .api.shop_dynamic import router as shop_dynamic_router
from .api.webhook_event import router as webhooks_router
from .api.user_service import router as users_router
from .api.product import router as product_router
from .api.session import router as session_router
from .api.setting import router as setting_router
from .api.audit import router as audit_router
from .api.webhook_event import router as webhook_event_router
from .api.analytics import router as merchant_analytics_router
from .api.coupon import router as coupon_router
from .api.dashboard import router as dashboard_router
from .api.notification import router as notification_router
from .api.scheduler import router as scheduler_router
from .api.team import router as team_router
from .api.usage import router as usage_router
from .api.brand_voice import router as brand_voice_router
from .api.learning_source import router as learning_source_router
from .api.user_feedback import router as user_feedback_router
from .api.calender import router as calendar_router
from .api.subscription import router as subscription_router  # Uncomment if needed
from .api.role_management import router as role_management_router
from .api.permission import router as permission_router
from .api.seo import router as seo_router
from .api.auth import router as auth_router
from .api.agency import router as agency_router
from .api.approval import router as approval_router
from .api.reporting import router as reporting_router
from .api.brand_voice_scraper import router as brand_voice_scraper_router
from .api.competitive_analysis import router as competitive_analysis_router
from .api.content_version_routes import router as content_version_router
from .api.gdpr import router as gdpr_router
from .api.consent import router as consent_router
from .api.data_retention import router as data_retention_router
from .jobs.job_runner import start_scheduler, stop_scheduler
from .database import engine, Base

# Load environment variables
load_dotenv()

# Shopify and App URL configuration
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_SCOPES = os.getenv("SHOPIFY_SCOPES")
APP_URL = os.getenv("APP_URL")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET")


async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # It's recommended to manage your database schema with Alembic migrations
    # instead of using Base.metadata.create_all().
    # Run `alembic upgrade head` to apply migrations before starting the app.
    await init_db()
    start_scheduler()
    yield
    stop_scheduler()


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


app = FastAPI(lifespan=lifespan)
from .api.user_status import router as user_status_router

from fastapi.responses import RedirectResponse

# Root route now redirects to frontend
@app.get("/")
async def root():
    return RedirectResponse(url="http://localhost:5173/")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "shopify-saas-app"}

app.state.APP_URL = APP_URL
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.include_router(user_status_router, prefix="/api")

# --- Add Middleware ---
add_cors_middleware(app)  # Update allowed_origins in middleware/cors.py with your public tunnel URL for Shopify
add_logging_middleware(app)
add_exception_handlers(app)

app.add_middleware(AuthMiddleware)

# Add Rate Limiting Middleware
app.add_middleware(RateLimitingMiddleware)
app.add_middleware(RequestValidationMiddleware, shopify_secret=SHOPIFY_API_SECRET)

# --- Include Routers ---
app.include_router(shopify_openai_router)
app.include_router(shop_dynamic_router)
app.include_router(webhooks_router)
app.include_router(users_router)
app.include_router(product_router)
app.include_router(session_router)
app.include_router(setting_router)
app.include_router(audit_router)
app.include_router(webhook_event_router)
app.include_router(merchant_analytics_router)
app.include_router(coupon_router)
app.include_router(dashboard_router)
app.include_router(notification_router)
app.include_router(scheduler_router)
app.include_router(team_router)
# app.include_router(subscription_router)
app.include_router(usage_router)
app.include_router(brand_voice_router)
app.include_router(learning_source_router)
app.include_router(user_feedback_router)
app.include_router(calendar_router)
app.include_router(subscription_router)
app.include_router(role_management_router)
app.include_router(permission_router)
app.include_router(seo_router)
app.include_router(auth_router)
app.include_router(agency_router)
app.include_router(approval_router)
app.include_router(reporting_router)
app.include_router(brand_voice_scraper_router)
app.include_router(competitive_analysis_router)
app.include_router(content_version_router)
app.include_router(gdpr_router)
app.include_router(consent_router)
app.include_router(data_retention_router)

# Import all models to ensure they are registered with SQLAlchemy's metadata
from .models import (
    ab_test,
    activity_log,
    agency,
    approval,
    associations,
    audit,
    billing,
    billing_history,
    brand_voice,
    consent,
    content_version,
    coupon,
    coupon_usage_log,
    custom_role,
    experiment,
    feedback,
    learning_source,
    memory_vault_entry,
    notification,
    permission,
    plan,
    product,
    report,
    role_model,
    role_version,
    scheduled_ab_test_rotation,
    scheduler,
    segment,
    segment_performance,
    seo_model,
    session,
    setting,
    shop,
    subscription,
    team,
    usage,
    usage_event,
    user,
    user_feedback,
    user_notification_preference,
    variant,
    webhook,
    webhook_event,
)

# Base.metadata.create_all(bind=engine)




# --- API Documentation Metadata ---
app.title = "Shopify SaaS App API"
app.description = "API for managing Shopify app users, products, sessions, webhooks, audits, and settings. All endpoints use Pydantic schemas for validation."
app.version = "1.0.0"
