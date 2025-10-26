"""
API routes for product CRUD operations.
"""

from typing import List
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .. import database
from ..schemas.product import ProductCreate, ProductRead, ProductUpdate
from ..services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(database.get_db)):
    """Create a new product."""
    service = ProductService(db)
    return service.create_product(product_data=product)


@router.get("/", response_model=List[ProductRead])
def list_products(
    db: Session = Depends(database.get_db), skip: int = 0, limit: int = 100
):
    """Retrieve a list of products."""
    service = ProductService(db)
    products = service.list_products(skip=skip, limit=limit)
    return products


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(database.get_db)):
    """Retrieve a single product by its ID."""
    service = ProductService(db)
    product = service.get_product(product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product


@router.put("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int, product: ProductUpdate, db: Session = Depends(database.get_db)
):
    """Update a product's details."""
    service = ProductService(db)
    return service.update_product(product_id=product_id, product_update=product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(database.get_db)):
    """Delete a product."""
    service = ProductService(db)
    service.delete_product(product_id=product_id)


@router.get("/view", response_class=HTMLResponse)
async def view_products(request: Request, db: Session = Depends(database.get_db)):
    """
    Display a list of products in an HTML view.
    """
    service = ProductService(db)
    products = service.list_products(skip=0, limit=100)
    return templates.TemplateResponse(
        "Product.html",
        {
            "request": request,
            "products": products,
            "app_url": request.app.state.APP_URL,
        },
    )
