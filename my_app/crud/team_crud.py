from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from ..schemas import team as schemas_team
from ..models.team import TeamMemberStatus, Team, TeamMember


# --- Team CRUD ---
def create_team(db: Session, team: schemas_team.TeamCreate, owner_id: int) -> Team:
    db_team = Team(**team.dict(), owner_id=owner_id)
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


def get_team(db: Session, team_id: int) -> Optional[Team]:
    return (
        db.query(Team)
        .options(
            joinedload(Team.members).joinedload(TeamMember.user),
            joinedload(Team.members).joinedload(TeamMember.role),
        )
        .filter(Team.id == team_id)
        .first()
    )


def get_teams_by_user(db: Session, user_id: int) -> List[Team]:
    return db.query(Team).filter(Team.owner_id == user_id).all()


def update_team(
    db: Session, team_id: int, team_update: schemas_team.TeamUpdate
) -> Optional[Team]:
    db_team = get_team(db, team_id)
    if db_team:
        for key, value in team_update.dict(exclude_unset=True).items():
            setattr(db_team, key, value)
        db.commit()
        db.refresh(db_team)
    return db_team


def delete_team(db: Session, team_id: int) -> bool:
    db_team = get_team(db, team_id)
    if db_team:
        db.delete(db_team)
        db.commit()
        return True
    return False


# --- Team Member CRUD ---
def create_team_member(
    db: Session,
    team_id: int,
    user_id: int,
    role_id: int,
    status: TeamMemberStatus = TeamMemberStatus.PENDING,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> TeamMember:
    db_member = TeamMember(
        team_id=team_id,
        user_id=user_id,
        role_id=role_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


def get_team_member(db: Session, team_id: int, user_id: int) -> Optional[TeamMember]:
    return (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
    )


def get_team_members(db: Session, team_id: int) -> List[TeamMember]:
    return db.query(TeamMember).filter(TeamMember.team_id == team_id).all()


def update_team_member_role(
    db: Session, team_id: int, user_id: int, role_id: int
) -> Optional[TeamMember]:
    db_member = get_team_member(db, team_id, user_id)
    if db_member:
        db_member.role_id = role_id
        db.commit()
        db.refresh(db_member)
    return db_member


def update_team_member_status(
    db: Session, team_id: int, user_id: int, status: TeamMemberStatus
) -> Optional[TeamMember]:
    db_member = get_team_member(db, team_id, user_id)
    if db_member:
        db_member.status = status
        db.commit()
        db.refresh(db_member)
    return db_member


def remove_team_member(db: Session, team_id: int, user_id: int) -> bool:
    db_member = get_team_member(db, team_id, user_id)
    if db_member:
        db.delete(db_member)
        db.commit()
        return True
    return False
