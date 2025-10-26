from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Any


class ProductUrlAnalysisRequest(BaseModel):
    url: HttpUrl
    primary_keyword: str


class SEOAnalysisResponse(BaseModel):
    url: HttpUrl
    title: str
    meta_description: Optional[str]
    readability_score: Optional[float]
    lsi_keywords: List[Any]
    tfidf_keywords: List[Any]
    overall_score: Optional[int]
    # Add more fields as needed
