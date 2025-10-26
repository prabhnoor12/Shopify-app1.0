from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud
from ..database import get_db
from ..models.user import User
from ..schemas.user_feedback import UserFeedbackCreate, UserFeedbackRead
from ..dependencies.auth import get_current_user

router = APIRouter()


@router.post("/user_feedback", response_model=UserFeedbackRead)
def create_user_feedback(
    *,
    db: Session = Depends(get_db),
    user_feedback_in: UserFeedbackCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Create new user feedback.
    """
    user_feedback = crud.user_feedback.create_with_user(
        db, obj_in=user_feedback_in, user_id=current_user.id
    )
    return user_feedback
