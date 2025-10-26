from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from .. import models, schemas


def create_custom_role(
    db: Session, custom_role: schemas.CustomRoleCreate, team_id: int
) -> models.CustomRole:
    db_custom_role = models.CustomRole(
        **custom_role.dict(exclude={"permission_ids"}), team_id=team_id
    )
    for perm_id in custom_role.permission_ids:
        permission = db.query(models.Permission).get(perm_id)
        if permission:
            db_custom_role.permissions.append(permission)
    db.add(db_custom_role)
    db.commit()
    db.refresh(db_custom_role)
    return db_custom_role


def get_custom_role(db: Session, custom_role_id: int) -> Optional[models.CustomRole]:
    return (
        db.query(models.CustomRole)
        .options(joinedload(models.CustomRole.permissions))
        .filter(models.CustomRole.id == custom_role_id)
        .first()
    )


def get_custom_roles_by_team(
    db: Session, team_id: int, skip: int = 0, limit: int = 100
) -> List[models.CustomRole]:
    return (
        db.query(models.CustomRole)
        .filter(models.CustomRole.team_id == team_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_custom_role(
    db: Session, custom_role_id: int, custom_role_update: schemas.CustomRoleUpdate
) -> Optional[models.CustomRole]:
    db_custom_role = get_custom_role(db, custom_role_id)
    if db_custom_role:
        db_custom_role.name = custom_role_update.name
        db_custom_role.description = custom_role_update.description
        db_custom_role.permissions.clear()
        for perm_id in custom_role_update.permission_ids:
            permission = db.query(models.Permission).get(perm_id)
            if permission:
                db_custom_role.permissions.append(permission)
        db.commit()
        db.refresh(db_custom_role)
    return db_custom_role


def delete_custom_role(db: Session, custom_role_id: int) -> bool:
    db_custom_role = get_custom_role(db, custom_role_id)
    if db_custom_role:
        db.delete(db_custom_role)
        db.commit()
        return True
    return False
