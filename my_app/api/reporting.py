from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse
from datetime import datetime
import io

from ..database import get_db
from ..services.reporting_service import ReportingService
from  my_app.models.user import User
from ..utils.security import get_current_user

router = APIRouter(
    prefix="/reporting",
    tags=["reporting"],
    responses={404: {"description": "Not found"}},
)


@router.get("/agency/{agency_id}/report", response_class=StreamingResponse)
def download_agency_report(
    agency_id: int,
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generates and downloads a white-labeled PDF report for an agency.

    An agency member can only generate reports for their own agency.
    """
    # Permission check: Ensure the current user is part of the agency
    if not current_user.agency_id or current_user.agency_id != agency_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to generate reports for this agency.",
        )

    reporting_service = ReportingService(db)
    try:
        pdf_bytes = reporting_service.generate_agency_report(
            agency_id=agency_id, start_date=start_date, end_date=end_date
        )

        report_filename = f"Agency_Report_{agency_id}_{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={report_filename}"},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        # Log the exception e
        raise HTTPException(status_code=500, detail="Failed to generate report.")
