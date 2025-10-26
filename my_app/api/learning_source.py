from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud
from ..database import get_db
from ..models.user import User
from ..schemas.learning_source import LearningResourceCreate, LearningResourceRead
from ..dependencies.auth import get_current_user

router = APIRouter()


@router.post("/learning_sources", response_model=LearningResourceRead)
def create_learning_source(
    *,
    db: Session = Depends(get_db),
    learning_source_in: LearningResourceCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Create a new learning source for the current user.
    """
    learning_source = crud.learning_source.create_with_user(
        db, obj_in=learning_source_in, user_id=current_user.id
    )
    return learning_source
