"""
Template Registry Service

Central registry for demo templates backed by database.

Key features:
- Search templates by content matching
- Return top K options for user selection
- Explain match scores with human-readable reasons
- Support browsing with filters
"""

import logging
from typing import Dict, List, Optional, Callable
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class TemplateRegistry:
    """
    Central registry for demo templates backed by database.

    Key features:
    - Search templates by content matching
    - Return top K options for user selection
    - Explain match scores with human-readable reasons
    - Support browsing with filters
    """

    def __init__(self, db_session_factory: Callable):
        """
        Initialize template registry with database session factory.

        Args:
            db_session_factory: Callable that returns a database session
        """
        self.db_session_factory = db_session_factory

    def search_templates_for_user_selection(
        self,
        content_info: Dict,
        workflow_type: str,
        max_results: int = 5
    ) -> List[Dict]:
        """
        Search and score templates for user to choose from.

        Args:
            content_info: Dict with content information
            workflow_type: Type of workflow ('ppt_demo', 'website_pdf', 'website_concept')
            max_results: Maximum number of results to return

        Returns:
            List of dicts with template options:
            [
                {
                    "template_id": "sorting_visualization",
                    "display_name": "排序算法可视化",
                    "match_score": 0.85,
                    "match_reason": "匹配关键词: sorting, sort | 类别匹配: algorithm | 适合8年级",
                    "complexity": "medium",
                    "usage_count": 150,
                    "thumbnail": "/assets/templates/sorting_thumb.png"
                },
                ...
            ]
        """
        db = self.db_session_factory()
        try:
            from ..models.demo_template import DemoTemplate

            # Query all active templates for workflow
            templates = db.query(DemoTemplate).filter(
                DemoTemplate.workflow_type == workflow_type,
                DemoTemplate.is_active == True
            ).all()

            # Give every template a minimum base score to ensure nothing gets completely filtered
            # Also add a small bonus based on usage count to promote popular templates
            BASE_SCORE = 0.1
            USAGE_BONUS_WEIGHT = 0.01

            # Score each template
            scored_templates = []
            for template in templates:
                score = template.calculate_match_score(content_info)

                # Add base score to ensure no template is completely excluded
                # Add small bonus for popular templates
                usage_bonus = min((template.usage_count or 0) * USAGE_BONUS_WEIGHT, 0.1)
                final_score = max(score, BASE_SCORE) + usage_bonus

                match_reason = self._explain_match_score(template, content_info, score)

                scored_templates.append({
                    'template_id': template.template_id,
                    'display_name': template.display_name,
                    'name': template.name,
                    'match_score': round(final_score, 3),
                    'original_score': round(score, 3),  # Keep original for transparency
                    'match_reason': match_reason,
                    'complexity': template.complexity,
                    'usage_count': template.usage_count,
                    'thumbnail': template.preview_thumbnail_path,
                    'grade_levels': template.grade_levels,
                    'subject_area': template.subject_area
                })

            # Sort by score and return top K
            scored_templates.sort(key=lambda x: x['match_score'], reverse=True)

            # Fallback: if no templates found (shouldn't happen with base score), return random templates
            if not scored_templates:
                logger.warning(f"No templates scored for {workflow_type}, returning all active templates")
                # Return all templates with default low scores
                for template in templates[:max_results]:
                    scored_templates.append({
                        'template_id': template.template_id,
                        'display_name': template.display_name,
                        'name': template.name,
                        'match_score': 0.1,  # Minimal score
                        'original_score': 0.0,
                        'match_reason': "通用模板",
                        'complexity': template.complexity,
                        'usage_count': template.usage_count,
                        'thumbnail': template.preview_thumbnail_path,
                        'grade_levels': template.grade_levels,
                        'subject_area': template.subject_area
                    })

            # Ensure we always return at least some templates, up to max_results
            return scored_templates[:max_results]

        finally:
            db.close()

    def get_template_by_id(self, template_id: str):
        """
        Get a template by its template_id.

        Args:
            template_id: Unique template identifier

        Returns:
            DemoTemplate instance or None
        """
        db = self.db_session_factory()
        try:
            from ..models.demo_template import DemoTemplate

            return db.query(DemoTemplate).filter(
                DemoTemplate.template_id == template_id,
                DemoTemplate.is_active == True
            ).first()
        finally:
            db.close()

    def browse_templates(
        self,
        workflow_type: Optional[str] = None,
        category: Optional[str] = None,
        grade_level: Optional[int] = None,
        subject_area: Optional[str] = None,
        complexity: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Browse templates with optional filters.

        Args:
            workflow_type: Filter by workflow type
            category: Filter by category
            grade_level: Filter by grade level
            subject_area: Filter by subject area
            complexity: Filter by complexity ('simple', 'medium', 'complex')
            limit: Maximum results to return

        Returns:
            List of template dicts
        """
        db = self.db_session_factory()
        try:
            from ..models.demo_template import DemoTemplate

            query = db.query(DemoTemplate).filter(
                DemoTemplate.is_active == True
            )

            if workflow_type:
                query = query.filter(DemoTemplate.workflow_type == workflow_type)

            if subject_area:
                query = query.filter(DemoTemplate.subject_area == subject_area)

            if complexity:
                query = query.filter(DemoTemplate.complexity == complexity)

            # Get templates first to handle JSON filtering in Python
            templates = query.all()

            # Filter by category (JSON array field)
            if category:
                templates = [t for t in templates if category in (t.categories or [])]

            # Filter by grade level (JSON array field)
            if grade_level is not None:
                templates = [t for t in templates if grade_level in (t.grade_levels or [])]

            # Apply limit after filtering
            templates = templates[:limit]

            return [
                {
                    'template_id': t.template_id,
                    'display_name': t.display_name,
                    'name': t.name,
                    'workflow_type': t.workflow_type,
                    'complexity': t.complexity,
                    'subject_area': t.subject_area,
                    'grade_levels': t.grade_levels,
                    'categories': t.categories,
                    'usage_count': t.usage_count,
                    'thumbnail': t.preview_thumbnail_path
                }
                for t in templates
            ]

        finally:
            db.close()

    def _explain_match_score(self, template, content_info: Dict, score: float) -> str:
        """Generate human-readable match explanation."""
        reasons = []

        # Check keyword matches
        content_text = f"{content_info.get('title', '')} {content_info.get('description', '')}".lower()
        matched_keywords = [kw for kw in (template.keywords or [])
                          if kw.lower() in content_text]
        matched_keywords_zh = [kw for kw in (template.keywords_zh or [])
                              if kw.lower() in content_text]

        all_matched = matched_keywords + matched_keywords_zh
        if all_matched:
            reasons.append(f"匹配关键词: {', '.join(all_matched[:3])}")

        # Check category match
        content_category = content_info.get('category', content_info.get('demo_type', ''))
        if content_category and content_category in template.categories:
            reasons.append(f"类别匹配: {content_category}")

        # Check grade level
        content_grade = content_info.get('grade_level')
        if content_grade and content_grade in template.grade_levels:
            reasons.append(f"适合{content_grade}年级")

        # Check subject area
        content_subject = content_info.get('subject', '')
        if content_subject and content_subject.lower() in template.subject_area.lower():
            reasons.append(f"学科匹配: {template.subject_area}")

        # If no specific matches, provide helpful generic messages
        if not reasons:
            # Add template categories as a suggestion
            if template.categories:
                reasons.append(f"模板类别: {', '.join(template.categories[:2])}")
            # Add subject area
            if template.subject_area:
                reasons.append(f"适用学科: {template.subject_area}")
            # Add usage count if popular
            if template.usage_count and template.usage_count > 50:
                reasons.append(f"热门模板 (使用{template.usage_count}次)")
            else:
                reasons.append("通用交互式演示模板")

        return " | ".join(reasons) if reasons else "通用交互式演示模板"

    def update_template_usage(self, template_id: str):
        """
        Increment the usage count for a template.

        Args:
            template_id: Template identifier
        """
        db = self.db_session_factory()
        try:
            from ..models.demo_template import DemoTemplate

            template = db.query(DemoTemplate).filter(
                DemoTemplate.template_id == template_id
            ).first()

            if template:
                template.usage_count = (template.usage_count or 0) + 1
                db.commit()
                logger.info(f"Updated usage count for template {template_id}: {template.usage_count}")

        except Exception as e:
            logger.error(f"Error updating template usage: {e}")
            db.rollback()
        finally:
            db.close()


# Global template registry instance
_template_registry_instance = None


def get_template_registry(db_session_factory: Callable) -> TemplateRegistry:
    """
    Get or create the global template registry instance.

    Args:
        db_session_factory: Callable that returns a database session

    Returns:
        TemplateRegistry instance
    """
    global _template_registry_instance

    if _template_registry_instance is None:
        _template_registry_instance = TemplateRegistry(db_session_factory)

    return _template_registry_instance
