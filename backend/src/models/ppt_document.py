from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.core.database import Base

class PPTDocument(Base):
    """Model for PPT/PPTX/PDF documents converted to interactive slides with demos."""

    __tablename__ = "ppt_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # 'pptx' or 'pdf'
    file_size = Column(BigInteger)
    slide_count = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String)
    grade_level = Column(Integer)
    description = Column(String)
    is_public = Column(Boolean, default=False)
    status = Column(String, default="processing")  # processing, ready, error

    # Store slide data and demo insertions
    # Structure:
    # {
    #   "slides": [
    #     {
    #       "slide_number": 1,
    #       "image_path": "uploads/ppt/{id}/slides/slide_1.png",
    #       "title": "Slide Title",
    #       "description": "Slide content summary",
    #       "needs_demo": false
    #     },
    #     {
    #       "slide_number": 2,
    #       "image_path": "uploads/ppt/{id}/slides/slide_2.png",
    #       "title": "Complex Concept",
    #       "description": "Slide content summary",
    #       "needs_demo": true,
    #       "demo_html": "<html>...</html>",
    #       "demo_reason": "Complex concept requires visualization",
    #       "demo_type": "simulation"
    #     }
    #   ]
    # }
    slides_data = Column(JSON, default=dict)

    # AI analysis results
    # {
    #   "overall_topic": "...",
    #   "target_audience": "...",
    #   "key_concepts": [...],
    #   "demo_insertion_strategy": "..."
    # }
    analysis_results = Column(JSON, default=dict)

    # Processing configuration
    # {
    #   "mode": "batch" | "specific_pages",
    #   "batch_size": 5,  # for batch mode
    #   "selected_pages": [1, 3, 5],  # for specific_pages mode
    #   "config_completed": false,  # true when user has configured
    #   "use_templates": true,  # enable template workflow
    #   "max_template_results": 3  # max template options per slide
    # }
    processing_config = Column(JSON, default=dict)

    # Template options for user selection (when status is "awaiting_template_selection")
    # {
    #   2: [  # slide_number
    #     {
    #       "template_id": "sorting_visualization",
    #       "display_name": "排序算法可视化",
    #       "match_score": 0.85,
    #       "match_reason": "..."
    #     },
    #     ...
    #   ],
    #   ...
    # }
    template_options = Column(JSON, default=dict)

    # Version management fields
    root_document_id = Column(Integer, ForeignKey("ppt_documents.id"), nullable=True)  # Root of version chain (null for root docs)
    version_number = Column(Integer, default=1)  # Version number in the chain
    is_current = Column(Integer, default=0)  # 1 = current version, 0 = not current

    # Store user prompt used for edits (latest prompt)
    user_prompt = Column(String, nullable=True)

    # Self-referential relationships
    root_document = relationship("PPTDocument", remote_side=[id], foreign_keys=[root_document_id])

    error_message = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<PPTDocument(id={self.id}, title='{self.title}', file_type='{self.file_type}', user_id={self.user_id})>"
