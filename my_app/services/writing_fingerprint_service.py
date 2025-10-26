from sqlalchemy.orm import Session
from .. import crud


class WritingFingerprintService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def get_writing_fingerprint_prompt(self) -> str:
        learning_sources = crud.learning_source.get_multi_by_user(
            self.db, user_id=self.user_id
        )
        if not learning_sources:
            return ""

        fingerprint = []
        for source in learning_sources:
            if source.content:
                fingerprint.append(source.content)

        return "\n".join(fingerprint)
