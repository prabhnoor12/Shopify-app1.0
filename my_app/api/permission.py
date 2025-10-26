from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from .. import schemas
from ..database import get_db
from ..services.role_service import RoleService
from ..dependencies.auth import get_current_user
from ..models.user import User as UserModel

router = APIRouter(
    prefix="/api/teams/{team_id}/permissions",
    tags=["permissions"],
    responses={404: {"description": "Not found"}},
)


def get_role_service(
    db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)
):
    return RoleService(db, current_user)


@router.get("/", response_model=List[schemas.Permission])
def read_permissions(
    team_id: int,
    service: RoleService = Depends(get_role_service),
):
    return service.get_permissions(team_id=team_id)
