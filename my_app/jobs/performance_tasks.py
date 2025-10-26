"""
This module contains Celery tasks for running performance analysis jobs.
"""
import logging
from my_app.database import SessionLocal
from my_app.services.product_service import ProductService
from my_app.services.audit_service import AuditLogService
from my_app.services.content_version_service import ContentVersionService
from ...celery_app import celery_app
from my_app.models.shop import ShopifyUser

logger = logging.getLogger(__name__)

@celery_app.task
def run_performance_analysis_for_shop(shop_id: int):
    """
    Celery task to run performance analysis for a single shop.
    """
    db = SessionLocal()
    try:
        audit_service = AuditLogService(db)
        content_version_service = ContentVersionService(db)
        product_service = ProductService(db, audit_service, content_version_service)

        import asyncio
        # Run analysis for the last 30 days by default
        asyncio.run(product_service.analyze_product_performance(shop_id, time_period_days=30))
    finally:
        db.close()

@celery_app.task
def run_performance_analysis_for_all_shops():
    """
    Kicks off performance analysis tasks for all shops in the database.
    """
    logger.info("Starting performance analysis for all shops.")
    db = SessionLocal()
    try:
        shops = db.query(ShopifyUser.id).all()
        for shop in shops:
            run_performance_analysis_for_shop.delay(shop.id)
    finally:
        db.close()
