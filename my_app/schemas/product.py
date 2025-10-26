"""
This module defines the Pydantic models for creating, reading, and updating
Product records, ensuring data validation and consistency.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class ProductBase(BaseModel):
    """Base schema for product attributes that are common to all variants.
    This schema is intended to be subclassed, not used directly.
    """

    shop_id: int
    shopify_product_id: str
    title: str
    slug: Optional[str] = None
    body_html: Optional[str] = None
    product_type: Optional[str] = None
    tags: Optional[str] = None
    vendor: Optional[str] = None
    status: Optional[str] = None
    price: Optional[float] = None
    is_published: Optional[bool] = True
    image_url: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    inventory_quantity: Optional[int] = None


class ProductCreate(ProductBase):
    """Schema for creating a new product. Inherits all fields from ProductBase.
    Use this schema when creating a new product to ensure all required fields are present.
    """

    pass


class ProductUpdate(BaseModel):
    """Schema for updating an existing product. All fields are optional.
    Use this schema when updating a product, as it allows for partial updates.
    """

    title: Optional[str] = None
    slug: Optional[str] = None
    body_html: Optional[str] = None
    product_type: Optional[str] = None
    tags: Optional[str] = None
    vendor: Optional[str] = None
    status: Optional[str] = None
    price: Optional[float] = None
    is_published: Optional[bool] = None
    image_url: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    inventory_quantity: Optional[int] = None


class Product(ProductBase):
    """Schema for reading product data, including database-generated fields.
    This schema is used for returning product data from the API.
    """

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ShopifyProductResponse(BaseModel):
    """Models the 'products' key in the Shopify API response."""

    products: List[Product]


class UpdateDescriptionPayload(BaseModel):
    """Defines the payload for the update description endpoint."""

    description: str = Field(min_length=2)


class ProductRead(BaseModel):
    """Schema for reading a single product's data.
    This schema is used for returning a single product's details from the API.
    """

    product: Product
    variant_id: Optional[int] = None
    variant: Optional[Product] = None


class ProductList(BaseModel):
    """Schema for a list of products.
    This schema is used for returning a list of products from the API.
    """

    products: List[Product]


class ProductPaginatedList(BaseModel):
    """Schema for a paginated list of products.
    This schema is used for returning a list of products with pagination details.
    """

    products: List[Product]
    total: int
