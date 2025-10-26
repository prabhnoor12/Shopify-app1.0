"""
This module contains the CRUD operations for the ApprovalRequest model.
"""

from sqlalchemy.orm import Session
from typing import Optional
from my_app.models.user import User
from my_app.models.approval import ApprovalRequest
from my_app import schemas

class ApprovalCRUD:
    def create_approval_request(
        self,
        db: Session,
        request: schemas.ApprovalRequestCreate,
        agency_id: int,
        requester_id: int,
    ) -> ApprovalRequest:
        db_request = ApprovalRequest(
            **request.dict(), agency_id=agency_id, requester_id=requester_id
        )
        db.add(db_request)
        db.commit()
        db.refresh(db_request)
        return db_request

    def get_approval_request_by_token(
        self, db: Session, token: str
    ) -> Optional[ApprovalRequest]:
        return (
            db.query(ApprovalRequest)
            .filter(ApprovalRequest.token == token)
            .first()
        )

    def update_approval_request_status(
        self, db: Session, token: str, response: schemas.ApprovalResponse
    ) -> Optional[ApprovalRequest]:
        db_request = self.get_approval_request_by_token(db, token)
        if db_request:
            db_request.status = response.status
            db_request.client_comment = response.comment
            db.commit()
            db.refresh(db_request)
        return db_request


approval_crud = ApprovalCRUD()
