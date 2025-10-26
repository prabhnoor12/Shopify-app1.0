from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..crud.brand_voice_crud import brand_voice
from ..database import get_db
from ..models.user import User
from ..schemas.brand_voice import BrandVoiceCreate, BrandVoiceRead
from ..dependencies.auth import get_current_user

router = APIRouter()


@router.post("/brand_voice", response_model=BrandVoiceRead)
def create_or_update_brand_voice(
    *,
    db: Session = Depends(get_db),
    brand_voice_in: BrandVoiceCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Create or update a brand voice for the current user.
    """
    brand_voice = brand_voice.get_by_user(db, user_id=current_user.id)
    if brand_voice:
        brand_voice = brand_voice.update(db, db_obj=brand_voice, obj_in=brand_voice_in)
    else:
        brand_voice = brand_voice.create_with_user(
            db, obj_in=brand_voice_in, user_id=current_user.id
        )
    return brand_voice


@router.get("/brand_voice", response_model=BrandVoiceRead)
def read_brand_voice(
    *, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get the brand voice for the current user.
    """
    brand_voice = brand_voice.get_by_user(db, user_id=current_user.id)
    if not brand_voice:
        raise HTTPException(status_code=404, detail="Brand voice not found")
    return brand_voice
