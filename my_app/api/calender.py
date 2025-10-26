from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from .. import schemas, crud
from ..dependencies.auth import get_current_user
from ..database import get_db
from ..models.user import User as UserModel
from ..services.team_service import TeamService

router = APIRouter(
    prefix="/api/teams/{team_id}/calendar",
    tags=["calendar"],
    responses={404: {"description": "Not found"}},
)


@router.get("/events", response_model=List[schemas.scheduler.ScheduledTaskWithUser])
def get_team_calendar_events(
    team_id: int,
    start_date: date,
    end_date: date,
    user_id: Optional[int] = Query(None, description="Filter events by user ID"),
    role_id: Optional[int] = Query(None, description="Filter events by role ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get calendar events for a team, with optional filtering by user or role.
    """
    # Check if the current user has permission to view the team calendar
    team_service = TeamService(db, current_user)
    if not team_service._has_permission(
        team_id, "calendar", "read", scope=str(team_id)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view team calendar",
        )

    # Convert date objects to datetime objects for the query
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    tasks = crud.scheduler.get_scheduled_tasks_for_team_in_range(
        db=db,
        team_id=team_id,
        start_date=start_datetime,
        end_date=end_datetime,
        user_id=user_id,
        role_id=role_id,
    )
    return tasks
