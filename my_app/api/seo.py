from fastapi import APIRouter, HTTPException
from ..services.seo_service import (
    analyze_product_url,
    SEOService,
    generate_seo_improvement_suggestions
)
from ..schemas.seo_schema import ProductUrlAnalysisRequest, SEOAnalysisResponse


router = APIRouter(prefix="/api/v1/seo", tags=["SEO"])



@router.post("/analyze-url", response_model=SEOAnalysisResponse)
async def analyze_url_endpoint(request: ProductUrlAnalysisRequest):
    """
    Analyzes a product URL for SEO metrics.
    """
    try:
        result = await analyze_product_url(
            url=str(request.url), primary_keyword=request.primary_keyword
        )
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        return SEOAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )

# Individual endpoints for each feature
from fastapi import Body

@router.post("/title-analysis")
async def title_analysis(request: ProductUrlAnalysisRequest):
    result = await analyze_product_url(url=str(request.url), primary_keyword=request.primary_keyword)
    return {"title": result.get("title")}

@router.post("/meta-description-analysis")
async def meta_description_analysis(request: ProductUrlAnalysisRequest):
    result = await analyze_product_url(url=str(request.url), primary_keyword=request.primary_keyword)
    return {"meta_description": result.get("meta_description")}

@router.post("/readability-score")
async def readability_score(request: ProductUrlAnalysisRequest):
    result = await analyze_product_url(url=str(request.url), primary_keyword=request.primary_keyword)
    return {"readability_score": result.get("readability_score")}

@router.post("/keyword-analysis")
async def keyword_analysis(request: ProductUrlAnalysisRequest):
    result = await analyze_product_url(url=str(request.url), primary_keyword=request.primary_keyword)
    return {
        "lsi_keywords": result.get("lsi_keywords"),
        "tfidf_keywords": result.get("tfidf_keywords")
    }

@router.post("/heading-analysis")
async def heading_analysis(request: ProductUrlAnalysisRequest):
    # For demo, extract main text from URL and analyze headings
    result = await analyze_product_url(url=str(request.url), primary_keyword=request.primary_keyword)
    # You may want to pass the HTML or main_text to analyze_headings
    return {"headings": SEOService.analyze_headings(result.get("meta_description", ""))}

@router.post("/image-analysis")
async def image_analysis(request: ProductUrlAnalysisRequest):
    result = await analyze_product_url(url=str(request.url), primary_keyword=request.primary_keyword)
    return {"images": SEOService.analyze_images(result.get("meta_description", ""))}

@router.post("/link-analysis")
async def link_analysis(request: ProductUrlAnalysisRequest, your_domain: str = Body(...)):
    result = await analyze_product_url(url=str(request.url), primary_keyword=request.primary_keyword)
    return {"links": SEOService.analyze_links(result.get("meta_description", ""), your_domain)}

@router.post("/ai-suggestions")
async def ai_suggestions(request: ProductUrlAnalysisRequest):
    result = await analyze_product_url(url=str(request.url), primary_keyword=request.primary_keyword)
    # You may need to pass a valid OpenAI client here
    suggestions = generate_seo_improvement_suggestions(openai_client=None, analysis_results=result)
    return {"suggestions": suggestions}
