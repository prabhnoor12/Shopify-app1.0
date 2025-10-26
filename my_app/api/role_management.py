from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..services.role_service import RoleService
from ..dependencies.auth import get_current_user
from ..models.user import User as UserModel
from .. import schemas

router = APIRouter(
    prefix="/api/teams/{team_id}/roles",
    tags=["roles"],
    responses={404: {"description": "Not found"}},
)


def get_role_service(
    db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)
):
    return RoleService(db, current_user)


@router.post("/", response_model=schemas.Role, status_code=status.HTTP_201_CREATED)
def create_role(
    team_id: int,
    role: schemas.RoleCreate,
    service: RoleService = Depends(get_role_service),
):
    return service.create_role(team_id=team_id, role_create=role)


@router.get("/", response_model=List[schemas.Role])
def read_roles(
    team_id: int,
    service: RoleService = Depends(get_role_service),
):
    return service.get_roles(team_id=team_id)


@router.get("/{role_id}", response_model=schemas.Role)
def read_role(
    team_id: int,
    role_id: int,
    service: RoleService = Depends(get_role_service),
):
    return service.get_role(team_id=team_id, role_id=role_id)


@router.put("/{role_id}", response_model=schemas.Role)
def update_role(
    team_id: int,
    role_id: int,
    role_update: schemas.RoleUpdate,
    service: RoleService = Depends(get_role_service),
):
    return service.update_role(
        team_id=team_id, role_id=role_id, role_update=role_update
    )


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    team_id: int,
    role_id: int,
    service: RoleService = Depends(get_role_service),
):
    service.delete_role(team_id=team_id, role_id=role_id)
    return
