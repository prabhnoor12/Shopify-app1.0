from sqlalchemy.orm import Session
from typing import List, Optional

from ..models.permission import Permission
from ..schemas.permission import PermissionCreate, PermissionUpdate


def get_permission(db: Session, permission_id: int) -> Optional[Permission]:
    return db.query(Permission).filter(Permission.id == permission_id).first()


def get_permission_by_details(
    db: Session, resource: str, action: str, scope: Optional[str] = None
) -> Optional[Permission]:
    return (
        db.query(Permission)
        .filter(
            Permission.resource == resource,
            Permission.action == action,
            Permission.scope == scope,
        )
        .first()
    )


def get_permissions(db: Session, skip: int = 0, limit: int = 100) -> List[Permission]:
    return db.query(Permission).offset(skip).limit(limit).all()


def create_permission(db: Session, permission: PermissionCreate) -> Permission:
    db_permission = Permission(
        resource=permission.resource, action=permission.action, scope=permission.scope
    )
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission


def update_permission(
    db: Session, permission_id: int, permission: PermissionUpdate
) -> Optional[Permission]:
    db_permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if db_permission:
        db_permission.resource = permission.resource
        db_permission.action = permission.action
        db_permission.scope = permission.scope
        db.commit()
        db.refresh(db_permission)
    return db_permission


def delete_permission(db: Session, permission_id: int) -> Optional[Permission]:
    db_permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if db_permission:
        db.delete(db_permission)
        db.commit()
    return db_permission
