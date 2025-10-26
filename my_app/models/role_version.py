from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, JSON
from sqlalchemy.orm import relationship
from ..database import Base


class RoleVersion(Base):
    __tablename__ = "role_versions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    version = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    permissions = Column(JSON, nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id"))
    updated_at = Column(DateTime, default=func.now())

    role = relationship("Role", back_populates="versions")
    updated_by = relationship("User")
