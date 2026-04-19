from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from src.core.database import Base

class ContentSection(Base):
    __tablename__ = "content_sections"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    section_type = Column(String, default="chapter")  # chapter, section, subsection
    order_index = Column(Integer, default=0)
    key_concepts = Column(JSON, default=list)
    learning_objectives = Column(JSON, default=list)
    section_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships will be added later to avoid circular imports

    def __repr__(self):
        return f"<ContentSection(id={self.id}, title='{self.title}', document_id={self.document_id})>"