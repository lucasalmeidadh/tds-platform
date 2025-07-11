from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from .database import Base

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    original_text = Column(Text, nullable=False)
    sentiment = Column(String)
    summary = Column(Text)
    suggested_response = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())