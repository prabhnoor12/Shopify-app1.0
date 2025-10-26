from typing import Optional

from sqlalchemy.orm import Session

from .base import CRUDBase
from ..models.brand_voice import BrandVoice
from ..schemas.brand_voice import BrandVoiceCreate, BrandVoiceUpdate


class CRUDBrandVoice(CRUDBase[BrandVoice, BrandVoiceCreate, BrandVoiceUpdate]):
    def get_by_user(self, db: Session, *, user_id: int) -> Optional[BrandVoice]:
        return db.query(BrandVoice).filter(BrandVoice.user_id == user_id).first()

    def create_with_user(
        self, db: Session, *, obj_in: BrandVoiceCreate, user_id: int
    ) -> BrandVoice:
        db_obj = BrandVoice(**obj_in.dict(), user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


brand_voice = CRUDBrandVoice(BrandVoice)
