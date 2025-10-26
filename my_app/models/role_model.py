from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from ..database import Base
from .role_version import RoleVersion
from .associations import role_permissions


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("name", "agency_id", name="_agency_role_name_uc"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    agency_id = Column(
        Integer, ForeignKey("agencies.id"), nullable=True
    )  # Nullable for global roles
    parent_role_id = Column(Integer, ForeignKey("roles.id"))

    agency = relationship("Agency", back_populates="roles")
    parent_role = relationship("Role", remote_side=[id])
    # Update the permissions relationship
    permissions = relationship(
        "Permission", secondary=role_permissions, back_populates="roles"
    )
    versions = relationship("RoleVersion", back_populates="role")
    # team_members relationship is now obsolete with the new model.
    team_members = relationship("TeamMember", back_populates="role")
