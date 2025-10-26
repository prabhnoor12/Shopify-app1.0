"""
This module provides the API endpoints for managing agencies, including
creating agencies, managing members, and managing clients.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from my_app.schemas.agency import (
    Agency, AgencyCreate, AgencyDetails, AgencyMember, AgencyMemberCreate, AgencyClient, AgencyClientCreate
)
from my_app.models.user import User
from ..database import get_db
from ..dependencies.auth import get_current_user
from ..services.agency_service import AgencyService

router = APIRouter(
    prefix="/agencies",
    tags=["agencies"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Agency, status_code=status.HTTP_201_CREATED)
def create_agency(
    agency: AgencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new agency. The user creating the agency will be its owner.
    """
    agency_service = AgencyService(db)
    return agency_service.create_agency(agency_create=agency, owner=current_user)


@router.get("/{agency_id}", response_model=AgencyDetails)
def read_agency(agency_id: int, db: Session = Depends(get_db)):
    """
    Retrieve details for a specific agency.
    """
    agency_service = AgencyService(db)
    db_agency = agency_service.get_agency_details(agency_id)
    if db_agency is None:
        raise HTTPException(status_code=404, detail="Agency not found")
    return db_agency


@router.post("/{agency_id}/members", response_model=AgencyMember)
def add_agency_member(
    agency_id: int,
    member: AgencyMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add a member to an agency. Only agency admins can perform this action.
    """
    agency_service = AgencyService(db)
    try:
        return agency_service.add_member(agency_id, member, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{agency_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_agency_member(
    agency_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove a member from an agency. Only agency admins can perform this action.
    """
    agency_service = AgencyService(db)
    try:
        if not agency_service.remove_member(agency_id, user_id, current_user):
            raise HTTPException(status_code=404, detail="Member not found")
    except (PermissionError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{agency_id}/clients", response_model=AgencyClient)
def add_agency_client(
    agency_id: int,
    client: AgencyClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add a client shop to an agency. Only agency members can perform this action.
    """
    agency_service = AgencyService(db)
    try:
        return agency_service.add_client(agency_id, client, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{agency_id}/clients/{shop_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_agency_client(
    agency_id: int,
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove a client shop from an agency. Only agency admins can perform this action.
    """
    agency_service = AgencyService(db)
    try:
        if not agency_service.remove_client(agency_id, shop_id, current_user):
            raise HTTPException(status_code=404, detail="Client not found")
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
