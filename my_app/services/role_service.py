import logging
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..schemas.role import Role, RoleCreate, RoleUpdate
from ..schemas.permission import Permission
from ..models.user import User
from .team_service import TeamService
from ..crud.role_crud import role as role_crud
from ..crud.permission_crud import get_permission

logger = logging.getLogger(__name__)


class RoleService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    def _get_team_service(self) -> TeamService:
        return TeamService(self.db, self.current_user)

    def create_role(self, team_id: int, role_create: RoleCreate) -> Role:
        team_service = self._get_team_service()
        if not team_service._has_permission(
            team_id, "role", "create", scope=str(team_id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to create a role",
            )

        try:
            # Use role_crud directly
            role = role_crud.create_role(
                db=self.db,
                role=role_create,
                team_id=team_id,
                updated_by_id=self.current_user.id,
            )
            self.db.commit()
            self.db.refresh(role)
            return Role.from_orm(role)
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Error creating role for team {team_id} by user {self.current_user.id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create role.",
            )

    def get_role(self, team_id: int, role_id: int) -> Role:
        team_service = self._get_team_service()
        if not team_service._has_permission(
            team_id, "role", "read", scope=str(team_id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view role",
            )

        # Use role_crud directly
        role = role_crud.get_role(db=self.db, role_id=role_id)
        if not role or role.team_id != team_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
            )
        return Role.from_orm(role)

    def get_roles(self, team_id: int) -> List[Role]:
        team_service = self._get_team_service()
        if not team_service._has_permission(
            team_id, "role", "read", scope=str(team_id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view roles",
            )

        # Use role_crud directly
        roles = role_crud.get_roles_by_team(db=self.db, team_id=team_id)
        return [Role.from_orm(role) for role in roles]

    def update_role(self, team_id: int, role_id: int, role_update: RoleUpdate) -> Role:
        team_service = self._get_team_service()
        if not team_service._has_permission(
            team_id, "role", "update", scope=str(team_id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update role",
            )

        # Verify role exists and belongs to the team before updating
        db_role = self.get_role(team_id, role_id)
        if not db_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
            )

        try:
            # Use role_crud directly
            role = role_crud.update_role(
                db=self.db,
                role_id=role_id,
                role_update=role_update,
                updated_by_id=self.current_user.id,
            )
            self.db.commit()
            self.db.refresh(role)
            return Role.from_orm(role)
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Error updating role {role_id} for team {team_id} by user {self.current_user.id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update role.",
            )

    def delete_role(self, team_id: int, role_id: int):
        team_service = self._get_team_service()
        if not team_service._has_permission(
            team_id, "role", "delete", scope=str(team_id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to delete role",
            )

        # Verify role exists and belongs to the team before deleting
        db_role = self.get_role(team_id, role_id)
        if not db_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
            )

        try:
            # Use role_crud directly
            role_crud.delete_role(db=self.db, role_id=role_id)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Error deleting role {role_id} for team {team_id} by user {self.current_user.id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete role.",
            )

    def get_permissions(self, team_id: int) -> List[Permission]:
        team_service = self._get_team_service()
        if not team_service._has_permission(
            team_id, "permission", "read", scope=str(team_id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view permissions",
            )

        # Use permission_crud directly
        permissions = get_permission(self.db)
        return [Permission.from_orm(p) for p in permissions]
