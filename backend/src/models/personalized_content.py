from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from src.core.database import Base

class PersonalizedContent(Base):
    __tablename__ = "personalized_content"

    id = Column(Integer, primary_key=True, index=True)
    content_section_id = Column(Integer, ForeignKey("content_sections.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    learning_mode = Column(String, nullable=False)  # immersive-text, slides, audio, mindmap, assessment
    personalized_content = Column(JSON, nullable=False)
    personalization_metadata = Column(JSON, default=dict)
    grade_level_adapted = Column(Integer)
    interests_applied = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships will be added later to avoid circular imports

    def __repr__(self):
        return f"<PersonalizedContent(id={self.id}, learning_mode='{self.learning_mode}', user_id={self.user_id})>"