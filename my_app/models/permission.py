from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from ..database import Base
from .associations import role_permissions


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    resource = Column(String, index=True, nullable=False)
    action = Column(String, index=True, nullable=False)
    scope = Column(
        String, nullable=True
    )  # For fine-grained permissions (e.g., product_id, category_id)

    roles = relationship(
        "Role", secondary=role_permissions, back_populates="permissions"
    )

    def __repr__(self):
        return f"<Permission(resource='{self.resource}', action='{self.action}', scope='{self.scope}')>"
