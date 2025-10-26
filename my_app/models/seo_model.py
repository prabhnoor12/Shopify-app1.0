from sqlalchemy import Column, Integer, String, Text
from ..database import Base


class SEOAnalysis(Base):
    __tablename__ = "seo_analysis"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    primary_keyword = Column(String, nullable=False)
    title = Column(String)
    meta_description = Column(Text)
    readability_score = Column(Integer)
    lsi_keywords = Column(Text)
    tfidf_keywords = Column(Text)
    overall_score = Column(Integer)

    # Add more fields as needed based on service output
