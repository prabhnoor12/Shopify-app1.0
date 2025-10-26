from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ..database import Base
import datetime


class Usage(Base):
    __tablename__ = "usage"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(
        Integer, ForeignKey("teams.id"), nullable=True
    )  # Make nullable if not all usage is team-specific
    user_id = Column(Integer, ForeignKey("users.id"))

    # Specific usage metrics
    descriptions_generated_short = Column(Integer, default=0)
    descriptions_generated_long = Column(Integer, default=0)
    images_processed_sd = Column(Integer, default=0)
    images_processed_hd = Column(Integer, default=0)
    brand_voices_created = Column(Integer, default=0)
    brand_voice_edited = Column(Integer, default=0)  # New sub-action
    analytics_reports_generated = Column(Integer, default=0)
    api_calls_made = Column(Integer, default=0)
    storage_used_mb = Column(Integer, default=0)  # Example for memory vault or similar

    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    last_activity_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    team = relationship("Team", back_populates="usage")
    user = relationship("User", back_populates="usage")
