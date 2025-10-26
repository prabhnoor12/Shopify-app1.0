from typing import List

from sqlalchemy.orm import Session

from .base import CRUDBase
from ..models.learning_source import LearningSource
from ..schemas.learning_source import LearningSourceCreate, LearningSourceUpdate


class CRUDLearningSource(
    CRUDBase[LearningSource, LearningSourceCreate, LearningSourceUpdate]
):
    def create_with_user(
        self, db: Session, *, obj_in: LearningSourceCreate, user_id: int
    ) -> LearningSource:
        db_obj = LearningSource(**obj_in.dict(), user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[LearningSource]:
        return (
            db.query(LearningSource)
            .filter(LearningSource.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


learning_source = CRUDLearningSource(LearningSource)
