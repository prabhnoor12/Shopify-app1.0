
"""
API routes for user management and queries.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from ..database import get_db
from ..services.user_service import UserService
from ..schemas.user import UserCreate, UserUpdate, UserRead, PasswordUpdate, ProfileUpdate

router = APIRouter(prefix="/users", tags=["users"])


    # Add more fields as needed

@router.post("/{user_id}/activate", response_model=UserRead)
def activate_user(user_id: int, db: Session = Depends(get_db)):
    service = UserService(db)
    user = service.activate_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.post("/{user_id}/deactivate", response_model=UserRead)
def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    service = UserService(db)
    user = service.deactivate_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.post("/{user_id}/password", response_model=UserRead)
def update_password(user_id: int, payload: PasswordUpdate, db: Session = Depends(get_db)):
    service = UserService(db)
    user = service.update_password(user_id, payload.new_password)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.post("/{user_id}/last-login", response_model=UserRead)
def update_last_login(user_id: int, db: Session = Depends(get_db)):
    service = UserService(db)
    user = service.update_last_login(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.put("/{user_id}/profile", response_model=UserRead)
def update_profile(user_id: int, profile: ProfileUpdate, db: Session = Depends(get_db)):
    service = UserService(db)
    user = service.update_profile(user_id, profile.dict(exclude_unset=True))
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user
"""
API routes for user management and queries.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..services.user_service import UserService
from ..schemas.user import UserCreate, UserUpdate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserRead])
def list_users(db: Session = Depends(get_db)):
    service = UserService(db)
    return service.list_users()


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    service = UserService(db)
    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.post("/", response_model=UserRead)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    service = UserService(db)
    return service.create_user(user.dict())


@router.put("/{user_id}", response_model=UserRead)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    service = UserService(db)
    user = service.update_user(user_id, user_update.dict(exclude_unset=True))
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    service = UserService(db)
    user = service.delete_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"detail": "User deleted"}


@router.get("/{shop_domain}/stats")
def get_user_stats(shop_domain: str, db: Session = Depends(get_db)):
    """Get usage stats for a user."""
    service = UserService(db)
    stats = service.get_user_stats(shop_domain)
    if not stats:
        raise HTTPException(status_code=404, detail="User not found.")
    return stats


@router.get("/search/", response_model=List[UserRead])
def search_users(query: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    service = UserService(db)
    return service.search_users(query)
