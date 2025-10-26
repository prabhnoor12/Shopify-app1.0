from typing import List
from sqlalchemy.orm import Session
from .. import models
from ..models.role_version import RoleVersion as RoleVersionModel
from ..schemas.role_version import RoleVersionCreate


def create_role_version(
    db: Session, role_version: RoleVersionCreate
) -> RoleVersionModel:
    db_role_version = RoleVersionModel(**role_version.model_dump())
    db.add(db_role_version)
    db.commit()
    db.refresh(db_role_version)
    return db_role_version


def get_role_versions_by_role(
    db: Session, role_id: int, skip: int = 0, limit: int = 100
) -> List[models.RoleVersion]:
    return (
        db.query(models.RoleVersion)
        .filter(models.RoleVersion.role_id == role_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
