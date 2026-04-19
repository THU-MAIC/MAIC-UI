from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.core.database import Base

# Maximum number of versions to keep per document chain
MAX_VERSION_HISTORY = 10


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(BigInteger)
    page_count = Column(Integer, default=0)
    subject = Column(String)
    grade_level = Column(Integer, default=0)
    description = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)
    status = Column(String, default="processing")  # processing, ready, error
    pdf_metadata = Column(JSON, default=dict)
    processing_results = Column(JSON, default=dict)  # Store analysis, website, interactive elements
    error_message = Column(String)  # Store error details if processing fails
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Version management fields
    root_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)  # Root of version chain (null for root docs)
    version_number = Column(Integer, default=1)  # Version number in the chain
    is_current = Column(Integer, default=0)  # 1 = current version, 0 = not current

    # Store user prompt used for edits (latest prompt)
    user_prompt = Column(String, nullable=True)

    # Self-referential relationships
    root_document = relationship("Document", remote_side=[id], foreign_keys=[root_document_id])

    # Relationships will be added later to avoid circular imports

    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}', user_id={self.user_id})>"