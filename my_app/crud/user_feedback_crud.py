from sqlalchemy.orm import Session
import logging
from .base import CRUDBase
from ..models.user_feedback import UserFeedback
from ..schemas.user_feedback import UserFeedbackCreate, UserFeedbackUpdate

logger = logging.getLogger(__name__)


class CRUDUserFeedback(CRUDBase[UserFeedback, UserFeedbackCreate, UserFeedbackUpdate]):
    """
    CRUD operations for UserFeedback model.
    """

    def create_with_user(
        self, db: Session, *, obj_in: UserFeedbackCreate, user_id: int
    ) -> UserFeedback:
        """
        Create a UserFeedback entry for a specific user.
        """
        try:
            db_obj = UserFeedback(**obj_in.dict(), user_id=user_id)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Created UserFeedback for user_id={user_id}, id={db_obj.id}")
            return db_obj
        except Exception as e:
            logger.error(f"Error creating UserFeedback for user_id={user_id}: {e}")
            db.rollback()
            raise

    def get_multi_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[UserFeedback]:
        """
        Get multiple UserFeedback entries for a user.
        """
        try:
            feedback_list = (
                db.query(UserFeedback)
                .filter(UserFeedback.user_id == user_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
            logger.info(f"Fetched {len(feedback_list)} feedbacks for user_id={user_id}")
            return feedback_list
        except Exception as e:
            logger.error(f"Error fetching feedbacks for user_id={user_id}: {e}")
            return []


user_feedback = CRUDUserFeedback(UserFeedback)
