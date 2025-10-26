"""
This module contains the business logic for the client approval workflow.
"""

from sqlalchemy.orm import Session
from typing import Optional
import os

from my_app.models.user import User
from my_app.crud.approval_crud import approval_crud
from my_app.models.approval import ApprovalRequest, ApprovalStatus
from my_app.schemas.approval import ApprovalRequestCreate, ApprovalResponse
from my_app.services.agency_service import AgencyService


class ApprovalService:
    def __init__(self, db: Session):
        self.db = db
        self.agency_service = AgencyService(db)

    def create_approval_request(
        self,
        request_create: ApprovalRequestCreate,
        agency_id: int,
        requester: User,
    ) -> str:
        """
        Creates a new approval request and returns the secure, shareable link for the client.
        """
        # Ensure the requester is a member of the agency
        if not self.agency_service.is_user_agency_member(requester.id, agency_id):
            raise PermissionError("Only agency members can create approval requests.")

        request = approval_crud.create_approval_request(
            self.db,
            request=request_create,
            agency_id=agency_id,
            requester_id=requester.id,
        )

        # Construct the shareable link
        app_url = os.getenv("APP_URL", "http://localhost:3000")
        shareable_link = f"{app_url}/approve/{request.token}"

        # Here you could also trigger an email to the client
        # email_service.send_approval_request_email(client_email, shareable_link)

        return shareable_link

    def get_request_by_token(self, token: str) -> Optional[ApprovalRequest]:
        """
        Retrieves an approval request using the secure token.
        This is used by the client-facing page.
        """
        return approval_crud.get_approval_request_by_token(self.db, token)

    def process_client_response(
        self, token: str, response: ApprovalResponse
    ) -> Optional[ApprovalRequest]:
        """
        Processes the client's response (approve/reject) to a request.
        """
        # You might want to add logic here to check if the request is expired
        request = self.get_request_by_token(token)
        if not request or request.status != ApprovalStatus.PENDING:
            raise ValueError(
                "This approval request is not valid or has already been actioned."
            )

        updated_request = approval_crud.update_approval_request_status(
            self.db, token, response
        )

        # Here you could trigger a notification back to the agency/requester
        # notification_service.notify_agency_of_approval_response(request.agency_id, updated_request)

        return updated_request
