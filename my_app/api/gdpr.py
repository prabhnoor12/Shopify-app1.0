from fastapi import Body

# New endpoint for data erasure by email (for frontend integration)

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.user_service import UserService
from ..schemas.gdpr import GDPRDataRequest, GDPRDataResponse, GDPRRequestStatus, DataRectificationRequest
from ..utils.security import get_current_user  # Assuming this exists
import json
import uuid
from datetime import datetime

router = APIRouter(prefix="/gdpr", tags=["gdpr"])


@router.post("/data-request", response_model=GDPRRequestStatus)
async def request_data_access(
    request: GDPRDataRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Submit a GDPR data access or deletion request.
    In a real implementation, this would queue the request and send confirmation emails.
    """
    service = UserService(db)

    # Find user by email
    user = service.get_user_by_email(request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found with this email address.")

    # Generate request ID
    request_id = str(uuid.uuid4())

    # For demo purposes, we'll process immediately
    # In production, this should be queued and processed asynchronously
    if request.request_type == "access":
        data = service.export_user_data(user.id, format_type=request.format)
        if data:
            # In production, save to file and provide download URL
            return GDPRRequestStatus(
                request_id=request_id,
                status="completed",
                request_type="access",
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                download_url=f"/api/gdpr/download/{request_id}"  # Placeholder
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to export data.")
    elif request.request_type == "delete":
        success = service.delete_user_data(user.id)
        if success:
            return GDPRRequestStatus(
                request_id=request_id,
                status="completed",
                request_type="delete",
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to delete data.")
    else:
        raise HTTPException(status_code=400, detail="Invalid request type. Must be 'access' or 'delete'.")


@router.get("/data-export/{user_id}")
def get_data_export(user_id: int, format: str = "json", db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Get exported data for a user in the specified format (json, csv, xml).
    In production, this should require proper authentication and authorization.
    """
    if format not in ["json", "csv", "xml"]:
        raise HTTPException(status_code=400, detail="Invalid format. Supported formats: json, csv, xml")

    service = UserService(db)
    data = service.export_user_data(user_id, format_type=format)

    if not data:
        raise HTTPException(status_code=404, detail="User not found or no data available.")

    if format == "json":
        return data
    else:
        # For CSV and XML, return as plain text
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(data, media_type="text/plain")


@router.delete("/data/{user_id}")
def delete_user_data(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Delete all personal data for a user (requires authentication).
    In production, this should require proper authentication and confirmation.
    """
    service = UserService(db)
    success = service.delete_user_data(user_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete user data.")

    return {"detail": "User data has been deleted successfully."}


@router.put("/rectify-data")
async def rectify_user_data(request: DataRectificationRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Rectify/update personal data for a user.
    In production, this should require proper authentication and authorization.
    """
    service = UserService(db)

    # Find user by email
    user = service.get_user_by_email(request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found with this email address.")

    # Validate the field and new value
    if request.field == "email":
        # Basic email validation
        if "@" not in request.new_value or "." not in request.new_value:
            raise HTTPException(status_code=400, detail="Invalid email format.")
    elif request.field == "shop_domain":
        # Basic domain validation
        if not request.new_value or "." not in request.new_value:
            raise HTTPException(status_code=400, detail="Invalid shop domain format.")
    elif request.field not in ["email", "shop_domain", "plan"]:
        raise HTTPException(status_code=400, detail="Field not allowed for rectification.")

    success = service.rectify_user_data(user.id, request.field, request.new_value, request.reason)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update user data.")

    return {"detail": f"Successfully updated {request.field} for user."}

@router.post("/erase-data")
async def erase_data(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Erase all personal data for a user by email (right to be forgotten).
    """
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")
    service = UserService(db)
    user = service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found with this email address.")
    success = service.delete_user_data(user.id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete user data.")
    return {"detail": "User data has been deleted successfully."}
"""
API routes for GDPR compliance - data access and deletion requests.
"""
