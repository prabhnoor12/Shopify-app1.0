"""
This module contains the business logic for the Agency feature. It uses the
agency_crud module to interact with the database and enforces business rules
and permissions.
"""


from sqlalchemy.orm import Session
from typing import Optional, List
from my_app.models.user import User
from my_app.models.agency import Agency, AgencyMember, AgencyRole, AgencyClient
from my_app.schemas.agency import (
    AgencyCreate, AgencyUpdate, AgencyMemberCreate, AgencyMemberUpdate,
    AgencyMember as AgencyMemberSchema, AgencyClientCreate, AgencyClient as AgencyClientSchema
)
from my_app.schemas.notification import EventType
from my_app.services.audit_service import AuditLogService
from my_app.services.notification_service import NotificationService
from my_app.crud import agency_crud


class AgencyService:
    def __init__(
        self,
        db: Session,
        audit_log_service: AuditLogService,
        notification_service: NotificationService,
    ):
        self.db = db
        self.audit_log_service = audit_log_service
        self.notification_service = notification_service

    def create_agency(
        self, agency_create: AgencyCreate, owner: User
    ) -> Agency:
        """
        Creates a new agency and sets the creator as the owner and an admin member.
        """
        # Create the agency
        agency = agency_crud.create_agency(self.db, agency_create, owner.id)

        # Add the owner as the first member with an admin role
        # This action is part of agency creation, so one log entry is sufficient.
        agency_crud.add_agency_member(self.db, agency.id, owner.id)

        self.audit_log_service.log(
            user_id=owner.id,
            action="create_agency",
            target_entity="agency",
            target_id=agency.id,
            change_details={"name": agency.name, "owner_id": owner.id},
        )

        return agency

    def get_agency_details(self, agency_id: int) -> Optional[Agency]:
        """
        Retrieves detailed information about an agency, including members and clients.
        """
        return agency_crud.get_agency(self.db, agency_id)

    def add_member(
        self,
        agency_id: int,
        member_create: AgencyMemberCreate,
        current_user: User,
    ) -> AgencyMember:
        """
        Adds a new member to an agency. Only admins of the agency can add new members.
        """
        if not self.is_user_agency_admin(current_user.id, agency_id):
            raise PermissionError("Only agency admins can add new members.")

        new_member = agency_crud.add_agency_member(
            self.db, agency_id, member_create.user_id
        )

        self.audit_log_service.log(
            user_id=current_user.id,
            action="add_agency_member",
            target_entity="agency",
            target_id=agency_id,
            change_details={"added_user_id": new_member.user_id},
        )

        self.notification_service.create_notification(
            user_id=new_member.user_id,
            event_type=EventType.AGENCY_MEMBER_ADDED,
            data={"agency_id": agency_id, "added_by": current_user.id},
        )

        return new_member

    def update_member(
        self,
        agency_id: int,
        user_id: int,
        member_update: AgencyMemberUpdate,
        current_user: User,
    ) -> Optional[AgencyMember]:
        """
        Updates a member's role in an agency. Only admins can update member roles.
        An owner cannot have their role changed.
        """
        agency = agency_crud.get_agency(self.db, agency_id)
        if not agency or not self.is_user_agency_admin(current_user.id, agency_id):
            raise PermissionError("Only agency admins can update member roles.")

        if agency.owner_id == user_id:
            raise ValueError("The agency owner cannot have their role changed.")

        updated_member = agency_crud.update_agency_member(
            self.db, agency_id, user_id, member_update
        )

        if updated_member:
            self.audit_log_service.log(
                user_id=current_user.id,
                action="update_agency_member",
                target_entity="agency",
                target_id=agency_id,
                change_details={
                    "updated_user_id": user_id,
                    "new_role": member_update.role,
                },
            )

        return updated_member

    def remove_member(
        self, agency_id: int, user_to_remove_id: int, current_user: User
    ) -> bool:
        """
        Removes a member from an agency. Only admins can remove members.
        An owner cannot be removed.
        """
        agency = agency_crud.get_agency(self.db, agency_id)
        if not agency or not self.is_user_agency_admin(current_user.id, agency_id):
            raise PermissionError("Only agency admins can remove members.")

        if agency.owner_id == user_to_remove_id:
            raise ValueError("The agency owner cannot be removed.")

        success = agency_crud.remove_agency_member(
            self.db, agency_id, user_to_remove_id
        )

        if success:
            self.audit_log_service.log(
                user_id=current_user.id,
                action="remove_agency_member",
                target_entity="agency",
                target_id=agency_id,
                change_details={"removed_user_id": user_to_remove_id},
            )

        return success

    def add_client(
        self,
        agency_id: int,
        client_create: AgencyClientCreate,
        current_user: User,
    ) -> AgencyClient:
        """
        Adds a client (shop) to an agency's managed list.
        Only agency members can add clients.
        """
        if not self.is_user_agency_member(current_user.id, agency_id):
            raise PermissionError("Only agency members can add clients.")

        new_client = agency_crud.add_agency_client(
            self.db, agency_id, client_create
        )

        self.audit_log_service.log(
            user_id=current_user.id,
            action="add_agency_client",
            target_entity="agency",
            target_id=agency_id,
            change_details={"added_shop_id": new_client.shop_id},
        )

        self.notification_service.create_notification(
            user_id=current_user.id,  # Or notify all agency admins
            event_type=EventType.CLIENT_ADDED_TO_AGENCY,
            data={"agency_id": agency_id, "shop_id": new_client.shop_id},
        )

        return new_client

    def remove_client(
        self, agency_id: int, shop_id: int, current_user: User
    ) -> bool:
        """
        Removes a client from an agency's managed list.
        Only agency admins can remove clients.
        """
        if not self.is_user_agency_admin(current_user.id, agency_id):
            raise PermissionError("Only agency admins can remove clients.")

        success = crud.agency_crud.remove_agency_client(self.db, agency_id, shop_id)

        if success:
            self.audit_log_service.log(
                user_id=current_user.id,
                action="remove_agency_client",
                target_entity="agency",
                target_id=agency_id,
                change_details={"removed_shop_id": shop_id},
            )

        return success

    def is_user_agency_member(self, user_id: int, agency_id: int) -> bool:
        """
        Checks if a user is a member of a given agency.
        """
        member = (
            self.db.query(AgencyMember)
            .filter(
                AgencyMember.agency_id == agency_id,
                AgencyMember.user_id == user_id,
            )
            .first()
        )
        return member is not None

    def is_user_agency_admin(self, user_id: int, agency_id: int) -> bool:
        """
        Checks if a user is an admin of a given agency.
        """
        member = (
            self.db.query(AgencyMember)
            .filter(
                AgencyMember.agency_id == agency_id,
                AgencyMember.user_id == user_id,
                AgencyMember.role == AgencyRole.ADMIN,
            )
            .first()
        )
        return member is not None
