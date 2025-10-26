"""
This module contains Celery tasks for running periodic jobs, such as content audits.
"""
import logging
from sqlalchemy.orm import Session
from my_app.database import SessionLocal
from my_app.services.product_service import ProductService
from my_app.services.audit_service import AuditLogService
from my_app.services.content_version_service import ContentVersionService
from ...celery_app import celery_app
from my_app.models.product import Product
from openai import OpenAI
from my_app.dependencies.config import settings

logger = logging.getLogger(__name__)

@celery_app.task
def run_product_audit(product_id: int):
    """
    Celery task to run content audit for a single product.
    """
    db: Session = SessionLocal()
    try:
        # Note: You might need a way to get the OpenAI client here.
        # This could be a global client or initialized per task.
        openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

        audit_service = AuditLogService(db)
        content_version_service = ContentVersionService(db)
        product_service = ProductService(db, audit_service, content_version_service, openai_client)

        # The service method is async, so we need to run it in an event loop if Celery is sync.
        # A better approach would be to use an async Celery worker.
        # For simplicity here, we'll assume you have a way to run async code.
        # This is a placeholder for running the async method.
        import asyncio
        asyncio.run(product_service.run_content_audit(product_id))

    finally:
        db.close()

@celery_app.task
def run_full_content_audit():
    """
    Celery task to run content audit for all products.
    """
    logger.info("Starting full content audit for all products.")
    db: Session = SessionLocal()
    try:
        products = db.query(Product.id).all()
        for product in products:
            run_product_audit.delay(product.id)
    finally:
        db.close()
