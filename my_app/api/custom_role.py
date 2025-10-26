from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import schemas
from ..database import get_db
from ..services.team_service import TeamService
from ..dependencies.auth import get_current_user
from ..models import User as UserModel
from ..crud import custom_role as custom_role_crud

router = APIRouter(
    prefix="/api/teams/{team_id}/custom-roles",
    tags=["custom-roles"],
    responses={404: {"description": "Not found"}},
)


def get_team_service(
    db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)
):
    return TeamService(db, current_user)


@router.post(
    "/", response_model=schemas.CustomRole, status_code=status.HTTP_201_CREATED
)
def create_custom_role(
    team_id: int,
    custom_role: schemas.CustomRoleCreate,
    service: TeamService = Depends(get_team_service),
    db: Session = Depends(get_db),
):
    if not service._has_permission(team_id, "team.custom_role", "create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return custom_role_crud.create_custom_role(
        db, custom_role=custom_role, team_id=team_id
    )


@router.get("/", response_model=List[schemas.CustomRole])
def read_custom_roles(
    team_id: int,
    service: TeamService = Depends(get_team_service),
    db: Session = Depends(get_db),
):
    if not service._has_permission(team_id, "team.custom_role", "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return custom_role_crud.get_custom_roles_by_team(db, team_id=team_id)


@router.get("/{custom_role_id}", response_model=schemas.CustomRole)
def read_custom_role(
    team_id: int,
    custom_role_id: int,
    service: TeamService = Depends(get_team_service),
    db: Session = Depends(get_db),
):
    if not service._has_permission(team_id, "team.custom_role", "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    db_custom_role = custom_role_crud.get_custom_role(db, custom_role_id=custom_role_id)
    if db_custom_role is None or db_custom_role.team_id != team_id:
        raise HTTPException(status_code=404, detail="Custom role not found")
    return db_custom_role


@router.put("/{custom_role_id}", response_model=schemas.CustomRole)
def update_custom_role(
    team_id: int,
    custom_role_id: int,
    custom_role_update: schemas.CustomRoleUpdate,
    service: TeamService = Depends(get_team_service),
    db: Session = Depends(get_db),
):
    if not service._has_permission(team_id, "team.custom_role", "update"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    db_custom_role = custom_role_crud.get_custom_role(db, custom_role_id=custom_role_id)
    if db_custom_role is None or db_custom_role.team_id != team_id:
        raise HTTPException(status_code=404, detail="Custom role not found")
    return custom_role_crud.update_custom_role(
        db, custom_role_id=custom_role_id, custom_role_update=custom_role_update
    )


@router.delete("/{custom_role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_custom_role(
    team_id: int,
    custom_role_id: int,
    service: TeamService = Depends(get_team_service),
    db: Session = Depends(get_db),
):
    if not service._has_permission(team_id, "team.custom_role", "delete"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    db_custom_role = custom_role_crud.get_custom_role(db, custom_role_id=custom_role_id)
    if db_custom_role is None or db_custom_role.team_id != team_id:
        raise HTTPException(status_code=404, detail="Custom role not found")
    custom_role_crud.delete_custom_role(db, custom_role_id=custom_role_id)
    return
