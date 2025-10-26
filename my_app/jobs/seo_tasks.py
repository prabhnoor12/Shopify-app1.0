"""
This module contains Celery tasks for SEO-related jobs, such as generating alt-text
and finding related products.
"""
import logging
from my_app.database import SessionLocal
from my_app.services.product_service import ProductService
from my_app.services.audit_service import AuditLogService
from my_app.services.content_version_service import ContentVersionService
from ...celery_app import celery_app
from my_app.models.product import Product

logger = logging.getLogger(__name__)

@celery_app.task
def generate_alt_text_for_product(product_id: int):
    """
    Celery task to generate alt-text for a single product's images.
    """
    db = SessionLocal()
    try:
        audit_service = AuditLogService(db)
        content_version_service = ContentVersionService(db)
        product_service = ProductService(db, audit_service, content_version_service)

        import asyncio
        asyncio.run(product_service.generate_alt_text_for_product_images(product_id))
    finally:
        db.close()

@celery_app.task
def generate_related_products_for_product(product_id: int):
    """
    Celery task to generate related product recommendations for a single product.
    """
    db = SessionLocal()
    try:
        audit_service = AuditLogService(db)
        content_version_service = ContentVersionService(db)
        product_service = ProductService(db, audit_service, content_version_service)

        import asyncio
        asyncio.run(product_service.generate_related_product_recommendations(product_id))
    finally:
        db.close()

@celery_app.task
def run_seo_enhancements_for_all_products():
    """
    Kicks off SEO enhancement tasks for all products in the database.
    """
    logger.info("Starting SEO enhancement tasks for all products.")
    db = SessionLocal()
    try:
        products = db.query(Product.id).all()
        for product in products:
            generate_alt_text_for_product.delay(product.id)
            generate_related_products_for_product.delay(product.id)
    finally:
        db.close()
