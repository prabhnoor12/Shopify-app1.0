from pydantic import BaseModel, Field
from typing import Optional, Dict


class DynamicContentRequest(BaseModel):
    """
    Request schema for fetching dynamic, personalized content for a product page.
    """

    product_id: int = Field(
        ..., description="The Shopify ID of the product being viewed."
    )
    visitor_ip: Optional[str] = Field(
        None, description="The IP address of the storefront visitor."
    )
    referral_source: Optional[str] = Field(
        None, description="The HTTP referer URL, if available."
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "product_id": 123456789,
                    "visitor_ip": "8.8.8.8",
                    "referral_source": "https://www.google.com/",
                }
            ]
        }


class DynamicContentResponse(BaseModel):
    """
    Response schema containing the personalized snippets to be injected into the storefront.
    """

    location_snippets: Dict[str, str] = Field(
        ...,
        description="Key-value pairs for location-based text, e.g., {'spelling': 'Colour'}.",
    )
    scarcity_snippet: Optional[str] = Field(
        None, description="An urgency message if inventory is low, e.g., 'Only 5 left!'"
    )
    referral_snippet: Optional[str] = Field(
        None, description="A message tailored to the visitor's referral source."
    )
    social_proof_snippet: Optional[str] = Field(
        None,
        description="A message to build trust, e.g., 'Trending now: 150 people viewed this today.'",
    )
