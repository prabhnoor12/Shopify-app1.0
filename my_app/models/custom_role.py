from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, func
from sqlalchemy.orm import relationship
from ..database import Base

custom_role_permission_association = Table(
    "custom_role_permission_association",
    Base.metadata,
    Column("custom_role_id", Integer, ForeignKey("custom_roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True),
)


class CustomRole(Base):
    __tablename__ = "custom_roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    parent_role_id = Column(Integer, ForeignKey("custom_roles.id"), nullable=True)
    permissions = relationship(
        "Permission",
        secondary=custom_role_permission_association,
        backref="custom_roles",
    )
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    team = relationship("Team")
    parent_role = relationship("CustomRole", remote_side=[id])
