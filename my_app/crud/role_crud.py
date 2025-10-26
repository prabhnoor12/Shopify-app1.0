from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from .. import models
from ..core.roles import RoleTemplate
from .base import CRUDBase
from ..models.role_model import Role
from ..schemas.role import RoleCreate, RoleUpdate


class CRUDRole(CRUDBase[Role, RoleCreate, RoleUpdate]):
    def create_role(
        self, db: Session, *, role: RoleCreate, team_id: int, updated_by_id: int
    ) -> Role:
        db_role = Role(
            **role.model_dump(), team_id=team_id, updated_by_id=updated_by_id
        )
        db.add(db_role)
        # Permissions are handled separately after role creation if needed
        return db_role

    def get_role(self, db: Session, *, role_id: int) -> Optional[Role]:
        return (
            db.query(Role)
            .options(joinedload(Role.permissions))
            .filter(Role.id == role_id)
            .first()
        )

    def get_role_by_name(
        self, db: Session, *, name: str, team_id: int
    ) -> Optional[Role]:
        return db.query(Role).filter(Role.name == name, Role.team_id == team_id).first()

    def get_roles_by_team(
        self, db: Session, *, team_id: int, skip: int = 0, limit: int = 100
    ) -> List[Role]:
        return (
            db.query(Role)
            .filter(Role.team_id == team_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_role(
        self, db: Session, *, role_id: int, role_update: RoleUpdate, updated_by_id: int
    ) -> Optional[Role]:
        db_role = self.get_role(db, role_id=role_id)
        if db_role:
            update_data = role_update.model_dump(exclude_unset=True)
            update_data["updated_by_id"] = updated_by_id
            for field, value in update_data.items():
                setattr(db_role, field, value)

            if "permission_ids" in update_data:
                permissions = (
                    db.query(models.Permission)
                    .filter(models.Permission.id.in_(update_data["permission_ids"]))
                    .all()
                )
                db_role.permissions = permissions

            db.add(db_role)
        return db_role

    def delete_role(self, db: Session, *, role_id: int) -> bool:
        db_role = db.query(Role).filter(Role.id == role_id).first()
        if db_role:
            db.delete(db_role)
            return True
        return False

    def create_role_from_template(
        self,
        db: Session,
        *,
        role_template: RoleTemplate,
        team_id: int,
        updated_by_id: int,
    ) -> Role:
        role_create = RoleCreate(
            name=role_template.name, description=role_template.description
        )
        db_role = self.create_role(
            db, role=role_create, team_id=team_id, updated_by_id=updated_by_id
        )

        # This assumes permission_crud is available or permissions are created here
        # For simplicity, let's assume permissions are handled elsewhere or we add them now.
        # This part might need adjustment based on your permission_crud logic.

        return db_role


role = CRUDRole(Role)
