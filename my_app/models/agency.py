"""
This module defines the database models for the Agency feature, including
the Agency itself, its members, and the clients it manages.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..database import Base


class AgencyRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"


class Agency(Base):
    __tablename__ = "agencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship(
        "User", back_populates="owned_agencies", foreign_keys=[owner_id]
    )
    members = relationship(
        "AgencyMember", back_populates="agency", cascade="all, delete-orphan"
    )
    clients = relationship(
        "AgencyClient", back_populates="agency", cascade="all, delete-orphan"
    )
    roles = relationship("Role", back_populates="agency", cascade="all, delete-orphan")


class AgencyMember(Base):
    __tablename__ = "agency_members"

    agency_id = Column(Integer, ForeignKey("agencies.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    # The 'role' enum is removed in favor of the new granular MemberClientRole model.

    agency = relationship("Agency", back_populates="members")
    user = relationship("User", back_populates="agencies")
    client_roles = relationship(
        "MemberClientRole", back_populates="member", cascade="all, delete-orphan"
    )


class MemberClientRole(Base):
    __tablename__ = "member_client_roles"

    member_agency_id = Column(Integer, ForeignKey("agencies.id"), primary_key=True)
    member_user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    client_shop_id = Column(Integer, ForeignKey("shopify_users.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["member_agency_id", "member_user_id"],
            ["agency_members.agency_id", "agency_members.user_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["member_agency_id", "client_shop_id"],
            ["agency_clients.agency_id", "agency_clients.shop_id"],
            ondelete="CASCADE",
        ),
    )

    member = relationship("AgencyMember", back_populates="client_roles")
    client = relationship(
        "AgencyClient", back_populates="member_roles", overlaps="member_roles"
    )
    role = relationship("Role")  # A role can be assigned to many member/client combos


class AgencyClient(Base):
    __tablename__ = "agency_clients"

    agency_id = Column(Integer, ForeignKey("agencies.id"), primary_key=True)
    shop_id = Column(Integer, ForeignKey("shopify_users.id"), primary_key=True)

    agency = relationship("Agency", back_populates="clients")
    shop = relationship("ShopifyUser", back_populates="managing_agencies")
    member_roles = relationship(
        "MemberClientRole",
        back_populates="client",
        cascade="all, delete-orphan",
        overlaps="client",
    )
