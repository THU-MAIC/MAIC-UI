from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from src.core.database import Base

class LearningProgress(Base):
    __tablename__ = "learning_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    content_section_id = Column(Integer, ForeignKey("content_sections.id"), nullable=False)
    learning_mode = Column(String, nullable=False)
    status = Column(String, default="not_started")  # not_started, in_progress, completed
    progress_percentage = Column(Float, default=0.0)
    time_spent_seconds = Column(Integer, default=0)
    quiz_scores = Column(JSON, default=list)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    progress_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships will be added later to avoid circular imports

    def __repr__(self):
        return f"<LearningProgress(id={self.id}, status='{self.status}', progress={self.progress_percentage}%)>"