from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base
from typing import Dict, Optional
from pathlib import Path


class DemoTemplate(Base):
    """Database-backed demo template for PPT, website from PDF, and website from concept."""

    __tablename__ = "demo_templates"

    # Core identification
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    display_name = Column(String(200), nullable=False)

    # Template classification
    workflow_type = Column(String(50), nullable=False)  # 'ppt_demo', 'website_pdf', 'website_concept'
    categories = Column(JSON, default=list)  # ["algorithm", "mathematics", "science"]
    keywords = Column(JSON, default=list)
    keywords_zh = Column(JSON, default=list)

    # Educational metadata
    grade_levels = Column(JSON, default=list)  # [6, 7, 8, 9, 10, 11, 12]
    complexity = Column(String(20))  # "simple", "medium", "complex"
    subject_area = Column(String(100))  # "Computer Science", "Mathematics", etc.

    # Template file reference (HTML stored in files, not DB)
    html_template_path = Column(String(500), nullable=False)
    preview_thumbnail_path = Column(String(500))

    # LLM configuration for customization
    llm_config = Column(JSON, default=dict)  # {"provider": "zhipu", "model": "glm-4.7"}

    # Parameter schema for UI configuration
    parameter_schema = Column(JSON, default=dict)

    # Template content hints (helps LLM understand what to customize)
    customization_hints = Column(Text)

    # Template matching configuration
    matching_config = Column(JSON, default=dict)  # Weights for scoring factors

    # Version control
    version = Column(String(20), default="1.0.0")
    is_active = Column(Boolean, default=True)

    # Usage statistics
    usage_count = Column(Integer, default=0)
    average_rating = Column(Integer)  # 1-5 stars

    # Audit fields
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

    def get_html_template(self) -> str:
        """Load HTML template from file."""
        template_path = Path(self.html_template_path)

        # If path is relative, make it relative to the backend directory
        if not template_path.is_absolute():
            # Get the backend directory (parent of src directory)
            backend_dir = Path(__file__).parent.parent.parent
            template_path = backend_dir / template_path

        if template_path.exists():
            return template_path.read_text(encoding='utf-8')
        raise FileNotFoundError(f"Template HTML not found: {self.html_template_path}")

    def calculate_match_score(self, content_info: Dict) -> float:
        """Calculate template match score using configured weights."""
        weights = self.matching_config.get('weights', {
            'keywords': 0.4,
            'category': 0.3,
            'grade_level': 0.2,
            'subject': 0.1
        })

        score = 0.0

        # Keyword matching
        content_text = f"{content_info.get('title', '')} {content_info.get('description', '')}"
        all_keywords = (self.keywords or []) + (self.keywords_zh or [])
        keyword_matches = sum(1 for kw in all_keywords if kw.lower() in content_text.lower())
        if len(all_keywords) > 0:
            score += (keyword_matches / len(all_keywords)) * weights['keywords']

        # Category matching
        content_category = content_info.get('category', content_info.get('demo_type', ''))
        if content_category and content_category in self.categories:
            score += weights['category']

        # Grade level matching
        content_grade = content_info.get('grade_level', 6)
        if content_grade in self.grade_levels:
            score += weights['grade_level']

        # Subject area matching
        content_subject = content_info.get('subject', '')
        if content_subject and content_subject.lower() in self.subject_area.lower():
            score += weights['subject']

        return min(score, 1.0)

    def __repr__(self):
        return f"<DemoTemplate(id={self.id}, template_id='{self.template_id}', name='{self.display_name}')>"
