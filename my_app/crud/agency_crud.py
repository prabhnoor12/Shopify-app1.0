"""
This module contains the CRUD (Create, Read, Update, Delete) operations
for the Agency, AgencyMember, and AgencyClient models.
"""

from sqlalchemy.orm import Session
from typing import List, Optional

from ..models.agency import Agency, AgencyMember, AgencyClient
from .. import schemas

# --- Agency CRUD ---


def create_agency(
    db: Session, agency: schemas.AgencyCreate, owner_id: int
) -> Agency:
    db_agency = Agency(**agency.dict(), owner_id=owner_id)
    db.add(db_agency)
    db.commit()
    db.refresh(db_agency)
    return db_agency


def get_agency(db: Session, agency_id: int) -> Optional[Agency]:
    return db.query(Agency).filter(Agency.id == agency_id).first()


def get_agencies_by_owner(db: Session, owner_id: int) -> List[Agency]:
    return db.query(Agency).filter(Agency.owner_id == owner_id).all()


def update_agency(
    db: Session, agency_id: int, agency_update: schemas.AgencyUpdate
) -> Optional[Agency]:
    db_agency = get_agency(db, agency_id)
    if db_agency:
        update_data = agency_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_agency, key, value)
        db.commit()
        db.refresh(db_agency)
    return db_agency


def delete_agency(db: Session, agency_id: int) -> bool:
    db_agency = get_agency(db, agency_id)
    if db_agency:
        db.delete(db_agency)
        db.commit()
        return True
    return False


# --- Agency Member CRUD ---


def add_agency_member(
    db: Session, agency_id: int, member: schemas.AgencyMemberCreate
) -> AgencyMember:
    db_member = AgencyMember(agency_id=agency_id, **member.dict())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


def remove_agency_member(db: Session, agency_id: int, user_id: int) -> bool:
    db_member = (
        db.query(AgencyMember)
        .filter(
            AgencyMember.agency_id == agency_id,
            AgencyMember.user_id == user_id,
        )
        .first()
    )
    if db_member:
        db.delete(db_member)
        db.commit()
        return True
    return False


# --- Agency Client CRUD ---


def add_agency_client(
    db: Session, agency_id: int, client: schemas.AgencyClientCreate
) -> AgencyClient:
    db_client = AgencyClient(agency_id=agency_id, **client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


def remove_agency_client(db: Session, agency_id: int, shop_id: int) -> bool:
    db_client = (
        db.query(AgencyClient)
        .filter(
            AgencyClient.agency_id == agency_id,
            AgencyClient.shop_id == shop_id,
        )
        .first()
    )
    if db_client:
        db.delete(db_client)
        db.commit()
        return True
    return False


def get_clients_for_agency(db: Session, agency_id: int) -> List[AgencyClient]:
    """
    Retrieves all client associations for a given agency.
    """
    return (
        db.query(AgencyClient)
        .filter(AgencyClient.agency_id == agency_id)
        .all()
    )
