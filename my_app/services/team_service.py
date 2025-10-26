import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime

from .. import crud
from ..schemas.team import Team, TeamCreate, TeamUpdate, InvitationCreate
from ..schemas.activity_log import ActivityLogCreate
from ..models.user import User
from ..models.team import TeamMemberStatus
from ..models.role_model import Role
from ..services.notification_service import NotificationService
from ..utils.security import create_invitation_token, verify_invitation_token
from ..core.roles import ROLE_TEMPLATES

logger = logging.getLogger(__name__)


class TeamService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
        self.notification_service = NotificationService(db)

    def _check_permission_in_role(
        self, role: Role, resource: str, action: str, scope: Optional[str] = None
    ) -> bool:
        for permission in role.permissions:
            if permission.resource == resource and permission.action == action:
                # If scope is provided, it must match the permission's scope or the permission's scope must be None (global)
                if scope is not None:
                    if permission.scope == scope or permission.scope is None:
                        return True
                else:  # If no scope is provided, a permission with no scope (global) or matching scope is sufficient
                    if permission.scope is None:
                        return True
        if role.parent_role:
            return self._check_permission_in_role(
                role.parent_role, resource, action, scope
            )
        return False

    def _has_permission(
        self, team_id: int, resource: str, action: str, scope: Optional[str] = None
    ) -> bool:
        member = crud.team.get_team_member(
            self.db, team_id=team_id, user_id=self.current_user.id
        )
        if not member or member.status != TeamMemberStatus.ACCEPTED:
            return False

        now = datetime.utcnow()
        if member.start_date and member.start_date > now:
            return False
        if member.end_date and member.end_date < now:
            return False

        if member.role:
            return self._check_permission_in_role(member.role, resource, action, scope)
        return False

    def create_team(self, team_create: TeamCreate) -> Team:
        try:
            team = crud.team.create_team(
                self.db, team=team_create, owner_id=self.current_user.id
            )
            # Automatically add the owner as a team member with an 'Admin' role
            admin_role_template = ROLE_TEMPLATES["Admin"]
            admin_role = crud.team.get_role_by_name(
                self.db, name=admin_role_template["name"]
            )
            if not admin_role:
                admin_role = crud.team.create_role_from_template(
                    self.db,
                    role_template=admin_role_template,
                    updated_by_id=self.current_user.id,
                )
            crud.team.create_team_member(
                self.db,
                team_id=team.id,
                user_id=self.current_user.id,
                role_id=admin_role.id,
                status=TeamMemberStatus.ACCEPTED,
            )
            self.db.commit()
            self.db.refresh(team)
            return Team.from_orm(team)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating team for user {self.current_user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create team due to an unexpected error.",
            )

    def get_team(self, team_id: int) -> Team:
        if not self._has_permission(
            team_id, "team", "read", scope=str(team_id)
        ):  # Add scope for team-specific permission
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )
        team = crud.team.get_team(self.db, team_id=team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
            )
        return Team.from_orm(team)

    def get_user_teams(self) -> List[Team]:
        teams = crud.team.get_teams_by_user(self.db, user_id=self.current_user.id)
        return [Team.from_orm(team) for team in teams]

    def update_team(self, team_id: int, team_update: TeamUpdate) -> Team:
        if not self._has_permission(
            team_id, "team", "update", scope=str(team_id)
        ):  # Add scope
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )
        try:
            team = crud.team.update_team(
                self.db, team_id=team_id, team_update=team_update
            )
            if not team:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
                )
            self.db.commit()
            return Team.from_orm(team)
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Error updating team {team_id} by user {self.current_user.id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update team due to an unexpected error.",
            )

    def delete_team(self, team_id: int):
        if not self._has_permission(
            team_id, "team", "delete", scope=str(team_id)
        ):  # Add scope
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )
        try:
            crud.team.delete_team(self.db, team_id=team_id)
            self.db.commit()
            return
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Error deleting team {team_id} by user {self.current_user.id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete team due to an unexpected error.",
            )

    def invite_member(self, team_id: int, invitation: InvitationCreate):
        if not self._has_permission(
            team_id, "team.member", "create", scope=str(team_id)
        ):  # Add scope
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )

        try:
            user_to_invite = crud.user.get_user_by_email(
                self.db, email=invitation.email
            )
            if not user_to_invite:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            existing_member = crud.team.get_team_member(
                self.db, team_id=team_id, user_id=user_to_invite.id
            )
            if existing_member:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already a member of the team",
                )

            crud.team.create_team_member(
                self.db,
                team_id=team_id,
                user_id=user_to_invite.id,
                role_id=invitation.role_id,
                status=TeamMemberStatus.PENDING,
            )
            crud.activity_log.create_activity_log(
                self.db,
                activity_log=ActivityLogCreate(
                    team_id=team_id,
                    user_id=self.current_user.id,
                    action="member_invited",
                    details={
                        "invited_user_id": user_to_invite.id,
                        "role_id": invitation.role_id,
                    },
                ),
            )
            self.db.commit()  # Commit after all database operations for this method

            # Send notification/email with invitation link
            token = create_invitation_token(email=invitation.email, team_id=team_id)
            # TODO: Replace with actual email sending logic using self.notification_service
            # self.notification_service.send_email(to=invitation.email, subject="Team Invitation", body=f"You have been invited to join a team. Click here to accept: /accept-invitation?token={token}")
            print(
                f"Invitation link for {invitation.email}: /accept-invitation?token={token}"
            )

        except (
            HTTPException
        ):  # Re-raise HTTPExceptions as they are business logic errors
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Error inviting member {invitation.email} to team {team_id} by user {self.current_user.id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to invite member due to an unexpected error.",
            )

    def accept_invitation(self, token: str):
        try:
            payload = verify_invitation_token(token)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired invitation token",
                )

            email = payload.get("email")
            team_id = payload.get("team_id")
            user = crud.user.get_user_by_email(self.db, email=email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            member = crud.team.get_team_member(
                self.db, team_id=team_id, user_id=user.id
            )
            if not member or member.status != TeamMemberStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired invitation",
                )

            crud.team.update_team_member_status(
                self.db,
                team_id=team_id,
                user_id=user.id,
                status=TeamMemberStatus.ACCEPTED,
            )
            self.db.commit()

        except (
            HTTPException
        ):  # Re-raise HTTPExceptions as they are business logic errors
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error accepting invitation for token {token}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to accept invitation due to an unexpected error.",
            )
