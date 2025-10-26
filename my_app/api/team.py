from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List

from .. import schemas
from ..database import get_db
from ..services.team_service import TeamService
from ..dependencies.auth import get_current_user
from ..schemas.team import (
    TeamCreate,
    TeamUpdate,
    InvitationCreate,
    TeamMemberUpdate,
    TransferOwnershipRequest,
)
from ..models.user import User as UserModel

router = APIRouter(
    prefix="/api/teams",
    tags=["teams"],
    responses={404: {"description": "Not found"}},
)


def get_team_service(
    db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)
):
    return TeamService(db, current_user)


@router.post("/", response_model=schemas.Team, status_code=status.HTTP_201_CREATED)
def create_team(
    team: TeamCreate,
    service: TeamService = Depends(get_team_service),
):
    return service.create_team(team_create=team)


@router.get("/me", response_model=List[schemas.Team])
def read_teams_for_current_user(
    service: TeamService = Depends(get_team_service),
):
    return service.get_user_teams()


@router.get("/{team_id}", response_model=schemas.Team)
def read_team(
    team_id: int,
    service: TeamService = Depends(get_team_service),
):
    return service.get_team(team_id=team_id)


@router.put("/{team_id}", response_model=schemas.Team)
def update_team(
    team_id: int,
    team_update: TeamUpdate,
    service: TeamService = Depends(get_team_service),
):
    return service.update_team(team_id=team_id, team_update=team_update)


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: int,
    service: TeamService = Depends(get_team_service),
):
    service.delete_team(team_id=team_id)
    return


@router.post("/{team_id}/invitations", status_code=status.HTTP_204_NO_CONTENT)
def invite_team_member(
    team_id: int,
    invitation: InvitationCreate,
    service: TeamService = Depends(get_team_service),
):
    service.invite_member(team_id=team_id, invitation=invitation)
    return


@router.post("/invitations/accept", status_code=status.HTTP_204_NO_CONTENT)
def accept_invitation(
    token: str = Query(...),
    service: TeamService = Depends(get_team_service),
):
    service.accept_invitation(token=token)
    return


@router.put("/{team_id}/members/{user_id}/role", status_code=status.HTTP_204_NO_CONTENT)
def update_team_member_role(
    team_id: int,
    user_id: int,
    role_update: TeamMemberUpdate,  # Using a schema for the new role
    service: TeamService = Depends(get_team_service),
):
    service.update_member_role(
        team_id=team_id, user_id=user_id, role_id=role_update.role_id
    )
    return


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_team_member(
    team_id: int,
    user_id: int,
    service: TeamService = Depends(get_team_service),
):
    service.remove_member(team_id=team_id, user_id=user_id)
    return


@router.post("/{team_id}/transfer-ownership", status_code=status.HTTP_204_NO_CONTENT)
def transfer_ownership(
    team_id: int,
    request: TransferOwnershipRequest,
    service: TeamService = Depends(get_team_service),
):
    service.transfer_ownership(team_id=team_id, new_owner_id=request.new_owner_id)
    return
