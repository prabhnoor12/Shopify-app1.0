from pydantic import BaseModel, Field
from pydantic import ConfigDict
from typing import List, Optional
from datetime import datetime


class ProductRequest(BaseModel):
    """Request schema for fetching products."""

    shop_domain: str = Field(...)
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"shop_domain": "example-shop.myshopify.com"}]}
    )


class GenerateRequest(BaseModel):
    """Request schema for generating a product description."""

    product_id: int = Field(...)
    title: str = Field(...)
    tone: str = Field(
        ...,
        description="Primary tone for the description (e.g., 'friendly', 'professional'). Is overridden if a specific persona is provided.",
    )
    persona: Optional[str] = Field(
        None,
        description="The target customer persona to write for (e.g., 'budget-conscious student', 'luxury gift-giver').",
    )
    length: str = Field(...)
    style: Optional[str] = None
    keywords: Optional[List[str]] = Field(
        None, description="A list of keywords to include in the description."
    )
    brand_voice_examples: Optional[List[str]] = Field(
        None, description="A list of 3-5 existing descriptions to mimic brand voice."
    )
    brand_guidelines: Optional[str] = Field(
        None, description="Brand guidelines for the AI to follow."
    )
    num_variants: int = Field(
        1, description="Number of description variants to generate."
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "product_id": 123456789,
                    "title": "Awesome T-Shirt",
                    "tone": "friendly",
                    "length": "medium",
                    "style": "humorous",
                }
            ]
        }
    )


class SEOCheck(BaseModel):
    name: str
    score: int
    status: str
    message: str


class SEOAnalysis(BaseModel):
    overall_score: int
    checks: List[SEOCheck]


class GenerateResponse(BaseModel):
    """Response schema for generated product descriptions."""

    descriptions: List[str]
    keywords: List[str]
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    seo_analysis: Optional[SEOAnalysis] = None
    seo_suggestions: Optional[str] = None


class GenerateFromImageRequest(BaseModel):
    """Request schema for generating a product description from an image."""

    image_url: str = Field(..., description="URL of the product image to analyze.")
    tone: str = Field(
        ...,
        description="Desired tone for the description (e.g., 'professional', 'witty').",
    )
    length: str = Field(
        ...,
        description="Desired length for the description (e.g., 'short', 'medium', 'long').",
    )
    style: Optional[str] = Field(
        None, description="Writing style (e.g., 'narrative', 'technical')."
    )
    keywords: Optional[List[str]] = Field(
        None, description="A list of keywords to include in the description."
    )
    num_variants: int = Field(
        1, description="Number of description variants to generate."
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "image_url": "https://example.com/product_image.jpg",
                    "tone": "enthusiastic",
                    "length": "medium",
                    "keywords": ["sustainable", "hand-crafted", "eco-friendly"],
                }
            ]
        }
    )


class GenerateFromUrlRequest(BaseModel):
    """Request schema for generating a product description from a URL."""

    url: str = Field(..., description="URL of the product page to scrape.")
    title: str = Field(..., description="Product title to use for context.")
    tone: str = Field(
        ...,
        description="Desired tone for the description (e.g., 'professional', 'witty').",
    )
    length: str = Field(
        ...,
        description="Desired length for the description (e.g., 'short', 'medium', 'long').",
    )
    style: Optional[str] = Field(
        None, description="Writing style (e.g., 'narrative', 'technical')."
    )
    keywords: Optional[List[str]] = Field(
        None, description="A list of keywords to include in the description."
    )
    num_variants: int = Field(
        1, description="Number of description variants to generate."
    )
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "url": "https://supplier.com/product-page",
                    "title": "High-Performance Drone",
                    "tone": "technical",
                    "length": "long",
                    "keywords": ["4k camera", "30-min flight time", "gps"],
                }
            ]
        }
    )


class SaveRequest(BaseModel):
    """Request schema for saving a new product description."""

    product_id: int = Field(...)
    new_description: str = Field(...)
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "product_id": 123456789,
                    "new_description": "This is a great t-shirt for all occasions.",
                }
            ]
        }
    )


class BulkSaveRequest(BaseModel):
    """Request schema for saving multiple product descriptions."""

    requests: List[SaveRequest]


class BulkGenerateProduct(BaseModel):
    product_id: int
    title: str


class BulkGenerateRequest(BaseModel):
    """Request schema for generating multiple product descriptions."""

    products: List[BulkGenerateProduct]
    tone: str
    length: str
    style: Optional[str] = None
    keywords: Optional[List[str]] = None
    brand_voice_examples: Optional[List[str]] = None
    num_variants: int = 1


class BulkGenerateResponse(BaseModel):
    """Response schema for bulk generated product descriptions."""

    results: List[GenerateResponse]
    errors: List[int]  # List of product_ids that failed


class BulkSaveResponse(BaseModel):
    """Response schema for bulk saved product descriptions."""

    success: List[int]
    errors: List[int]


class BulkFindReplaceError(BaseModel):
    product_id: Optional[int]
    error: str


class BulkFindReplaceRequest(BaseModel):
    """Request schema for bulk find and replace."""

    find_text: str = Field(
        ..., description="The text to search for in product descriptions."
    )
    replace_text: str = Field(
        ..., description="The text to replace the found text with."
    )
    collection_id: Optional[int] = Field(
        None,
        description="If provided, only products in this collection will be affected.",
    )


class BulkFindReplaceResponse(BaseModel):
    """Response schema for bulk find and replace operation."""

    updated_products: List[int] = Field(
        ..., description="A list of product IDs that were successfully updated."
    )
    total_matches: int = Field(
        ..., description="The total number of products where the text was found."
    )
    errors: List[BulkFindReplaceError] = Field(
        [], description="A list of errors that occurred during the update."
    )


class RegenerateVariantRequest(BaseModel):
    """Request schema for regenerating a single variant."""

    product_id: int
    original_description: str
    feedback: str = Field(
        ..., description="Specific feedback or instructions for the revision."
    )
    tone: str
    length: str
    style: Optional[str] = None
    keywords: Optional[List[str]] = None


class ShopifyUserBase(BaseModel):
    shop_domain: str
    shop_name: Optional[str] = None
    email: Optional[str] = None
    country: Optional[str] = None
    plan: Optional[str] = None
    trial_ends_at: Optional[datetime] = None
    webhook_version: Optional[str] = None
    is_active: Optional[int] = 1


class ShopifyUserCreate(ShopifyUserBase):
    access_token: str


class ShopifyUserUpdate(ShopifyUserBase):
    access_token: Optional[str] = None


class ShopifyUserResponse(ShopifyUserBase):
    id: int
    generations_used: int
    installed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class BenefitOrientedRequest(BaseModel):
    """Request schema for transforming a feature into a benefit."""

    text: str = Field(..., description="The feature text to transform.")
    product_title: str = Field(..., description="The title of the product for context.")
    target_audience: Optional[str] = Field(
        None, description="The target audience for the product."
    )


class BenefitOrientedResponse(BaseModel):
    """Response schema for the benefit-oriented transformation."""

    benefit_text: str
