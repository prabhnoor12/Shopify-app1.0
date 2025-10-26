from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.competitive_analysis_service import CompetitiveAnalysisService

router = APIRouter(
    prefix="/competitive-analysis",
    tags=["competitive-analysis"],
    responses={404: {"description": "Not found"}},
)


class AnalysisRequest(BaseModel):
    base_url: HttpUrl
    competitor_urls: List[HttpUrl]


@router.post("/compare", status_code=200)
def compare_pages(
    request: AnalysisRequest,
    db: Session = Depends(get_db),
):
    """
    Performs a competitive analysis by comparing a base URL to competitor URLs.

    - **base_url**: Your product or page URL.
    - **competitor_urls**: A list of competitor URLs to analyze against.
    """
    analysis_service = CompetitiveAnalysisService(db_session=db)
    try:
        # Convert Pydantic HttpUrl objects to strings for the service
        base_url_str = str(request.base_url)
        competitor_urls_str = [str(url) for url in request.competitor_urls]

        comparison_report = analysis_service.compare_pages(
            base_url=base_url_str, competitor_urls=competitor_urls_str
        )
        return comparison_report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # In a real app, you'd want to log this exception.
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}"
        )
