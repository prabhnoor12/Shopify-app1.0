"""
API routes for settings CRUD operations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db

from ..schemas.setting import (
    SettingCreate,
    SettingRead,
    SettingUpdate,
)  # Added SettingUpdate
from ..services.setting_service import SettingService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.post("/", response_model=SettingRead)
def create_setting(setting: SettingCreate, db: Session = Depends(get_db)):
    service = SettingService(db)
    return service.create_setting(setting.dict())


@router.get("/", response_model=List[SettingRead])
def list_settings(db: Session = Depends(get_db)):
    service = SettingService(db)
    return service.list_settings()


@router.get("/{setting_id}", response_model=SettingRead)
def get_setting(setting_id: int, db: Session = Depends(get_db)):
    service = SettingService(db)
    setting = service.get_setting(setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found.")
    return setting


@router.put("/{setting_id}", response_model=SettingRead)  # New PUT endpoint
def update_setting(
    setting_id: int, setting: SettingUpdate, db: Session = Depends(get_db)
):
    """
    Update an existing setting's value.
    """
    service = SettingService(db)
    updated_setting = service.update_setting(
        setting_id, setting.dict(exclude_unset=True)
    )
    if not updated_setting:
        raise HTTPException(status_code=404, detail="Setting not found.")
    return updated_setting


@router.delete("/{setting_id}")
def delete_setting(setting_id: int, db: Session = Depends(get_db)):
    service = SettingService(db)
    setting = service.delete_setting(setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found.")
    return {"detail": "Setting deleted"}
