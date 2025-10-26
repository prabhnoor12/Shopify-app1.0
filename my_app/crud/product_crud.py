from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.product import Product
from ..schemas.product import ProductCreate, ProductUpdate


def get_product(db: Session, product_id: int) -> Optional[Product]:
    """
    Retrieves a product by its ID.

    Args:
        db (Session): The SQLAlchemy database session.
        product_id (int): The ID of the product to retrieve.

    Returns:
        Optional[Product]: The product if found, otherwise None.
    """
    return db.query(Product).filter(Product.id == product_id).first()


def get_products(db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
    """
    Retrieves a list of products with pagination.

    Args:
        db (Session): The SQLAlchemy database session.
        skip (int): The number of records to skip.
        limit (int): The maximum number of records to return.

    Returns:
        List[Product]: A list of products.
    """
    return db.query(Product).offset(skip).limit(limit).all()


def create_product(db: Session, product: ProductCreate) -> Product:
    """
    Creates a new product in the database.

    Args:
        db (Session): The SQLAlchemy database session.
        product (ProductCreate): The data for the new product.

    Returns:
        Product: The newly created product.
    """
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(
    db: Session, db_product: Product, product_in: ProductUpdate
) -> Product:
    """
    Updates an existing product in the database.

    Args:
        db (Session): The SQLAlchemy database session.
        db_product (Product): The existing product to update.
        product_in (ProductUpdate): The new data for the product.

    Returns:
        Product: The updated product.
    """
    update_data = product_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)

    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def delete_product(db: Session, product_id: int) -> Optional[Product]:
    """
    Deletes a product from the database by its ID.

    Args:
        db (Session): The SQLAlchemy database session.
        product_id (int): The ID of the product to delete.

    Returns:
        Optional[Product]: The deleted product if found, otherwise None.
    """
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product:
        db.delete(db_product)
        db.commit()
    return db_product
