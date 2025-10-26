from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Enum
from sqlalchemy.orm import relationship
from ..database import Base
from .usage import Usage

import enum


# Enum for Team Member Status
class TeamMemberStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", foreign_keys=[owner_id], back_populates="teams_owned")
    members = relationship(
        "TeamMember", back_populates="team", cascade="all, delete-orphan"
    )
    usage = relationship("Usage", back_populates="team", cascade="all, delete-orphan")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    status = Column(Enum(TeamMemberStatus), default=TeamMemberStatus.PENDING)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    invited_at = Column(DateTime, default=func.now())
    responded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")
    role = relationship("Role", back_populates="team_members")
