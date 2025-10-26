"""
This module provides the API endpoints for the client approval workflow.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from  my_app import schemas
from my_app.models.user import User
from my_app.models.approval import ApprovalStatus
from ..database import get_db
from ..dependencies.auth import get_current_user
from ..services.approval_service import ApprovalService

router = APIRouter(
    prefix="/approvals",
    tags=["approvals"],
    responses={404: {"description": "Not found"}},
)


# Endpoint for the agency to create a request
@router.post("/request/{agency_id}", response_model=dict)
def create_approval_request(
    agency_id: int,
    request_data: schemas.ApprovalRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new content approval request. Returns a secure, shareable link for the client.
    """
    approval_service = ApprovalService(db)
    try:
        shareable_link = approval_service.create_approval_request(
            request_create=request_data, agency_id=agency_id, requester=current_user
        )
        return {"shareable_link": shareable_link}
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# Endpoint for the client to view the request
@router.get("/{token}", response_model=schemas.ApprovalRequest)
def get_approval_request(token: str, db: Session = Depends(get_db)):
    """
    Retrieve an approval request using the secure token. This is for the client-facing view.
    """
    approval_service = ApprovalService(db)
    request = approval_service.get_request_by_token(token)
    if not request or request.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=404, detail="Approval request not found or already actioned"
        )
    return request


# Endpoint for the client to respond to the request
@router.post("/{token}/respond", response_model=schemas.ApprovalRequest)
def respond_to_approval_request(
    token: str,
    response: schemas.ApprovalResponse,
    db: Session = Depends(get_db),
):
    """
    Process a client's response (approve/reject) to an approval request.
    """
    approval_service = ApprovalService(db)
    try:
        updated_request = approval_service.process_client_response(token, response)
        if not updated_request:
            raise HTTPException(status_code=404, detail="Approval request not found")
        return updated_request
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
