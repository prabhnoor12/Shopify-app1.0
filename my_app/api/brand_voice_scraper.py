from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl

from ..database import get_db
from ..services.brand_voice_scraper_service import BrandVoiceScraperService

router = APIRouter(
    prefix="/brand-voice",
    tags=["brand-voice"],
    responses={404: {"description": "Not found"}},
)


class ScrapeRequest(BaseModel):
    url: HttpUrl


@router.post("/scrape", status_code=200)
def analyze_url(
    request: ScrapeRequest,
    db: Session = Depends(get_db),
):
    """
    Scrapes a URL to analyze its content and suggest a brand voice profile.
    - **url**: The URL of the page to analyze.
    """
    scraper_service = BrandVoiceScraperService(db=db)
    try:
        analysis_result = scraper_service.scrape_and_analyze(str(request.url))
        return analysis_result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        # In a real app, you'd want to log this exception.
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during scraping and analysis.",
        )
