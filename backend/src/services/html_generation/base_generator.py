"""
Base Generator Module

This module provides the abstract base class for all HTML generators.
Both FastGenerator and HeavyGenerator inherit from this class.


Date: 2025-01-15
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging
import re

logger = logging.getLogger(__name__)


class BaseGenerator(ABC):
    """
    Abstract base class for HTML generators.

    This class defines the common interface that all generators must implement.
    It provides shared utilities and enforces a consistent generation pattern.
    """

    def __init__(self, ai_provider):
        """
        Initialize the generator with an AI provider.

        Args:
            ai_provider: An instance of AIProvider (EnglishProvider, ZhipuProvider, etc.)
        """
        self.provider = ai_provider
        self.generation_metadata = {
            "mode": self.__class__.__name__,
            "stages_completed": 0,
            "refinements": {},
            "errors": []
        }

    @abstractmethod
    async def generate(self, pdf_images: List[Dict], analysis: Dict,
                     user_preferences: Dict) -> Dict[str, Any]:
        """
        Generate interactive HTML content.

        Args:
            pdf_images: List of page images with metadata
            analysis: Content analysis from PDF processing
            user_preferences: User preferences including language, grade level, etc.

        Returns:
            Dict containing:
                - html: Generated HTML string
                - metadata: Generation metadata
                - generation_info: Statistics about the generation process
        """
        pass

    def _ensure_language_settings(self, user_preferences: Dict) -> Dict:
        """
        Ensure language requirements are in user preferences based on user selection.

        Args:
            user_preferences: Original user preferences

        Returns:
            Updated preferences with appropriate language settings
        """
        prefs = user_preferences.copy()

        # Check if user explicitly selected English
        user_lang = prefs.get('language', 'zh')

        if user_lang == 'en':
            prefs.setdefault('language', 'en')
            prefs.setdefault('output_language', 'English')
            prefs.setdefault('target_language', 'English')
        else:
            # Default to Chinese
            prefs.setdefault('language', 'zh-CN')
            prefs.setdefault('output_language', '简体中文')
            prefs.setdefault('target_language', 'Chinese')

        return prefs

    def _generate_metadata(self, analysis: Dict, user_preferences: Dict) -> Dict:
        """
        Generate metadata for the output HTML.

        Args:
            analysis: Content analysis from PDF processing
            user_preferences: User preferences

        Returns:
            Metadata dictionary
        """
        return {
            "title": analysis.get("title", "Interactive Learning"),
            "subject": analysis.get("subject_area", "General"),
            "grade_level": user_preferences.get("grade_level", "K-12"),
            "language": user_preferences.get("output_language", "简体中文"),
            "difficulty": analysis.get("difficulty_level", "intermediate"),
            "key_concepts": analysis.get("key_concepts", []),
            "learning_objectives": analysis.get("learning_objectives", []),
            "generator_mode": self.generation_metadata["mode"]
        }

    def _update_generation_info(self, stage: str, completed: bool = True,
                               refinement_count: int = 0, error: Optional[str] = None):
        """
        Update generation metadata with progress information.

        Args:
            stage: Stage identifier (e.g., "stage1", "stage2")
            completed: Whether the stage completed successfully
            refinement_count: Number of refinement attempts used
            error: Error message if stage failed
        """
        if completed:
            self.generation_metadata["stages_completed"] += 1

        self.generation_metadata["refinements"][stage] = refinement_count

        if error:
            self.generation_metadata["errors"].append({
                "stage": stage,
                "error": error
            })

    def _get_subject_theme(self, analysis: Dict) -> Dict[str, str]:
        """
        Get color theme based on subject area.

        Args:
            analysis: Content analysis with subject_area

        Returns:
            Dictionary with primary and accent colors
        """
        subject = analysis.get("subject_area", "").lower()

        themes = {
            "math": {"primary": "#3B82F6", "accent": "#10B981"},
            "physics": {"primary": "#8B5CF6", "accent": "#F59E0B"},
            "chemistry": {"primary": "#06B6D4", "accent": "#EC4899"},
            "language": {"primary": "#EC4899", "accent": "#06B6D4"},
            "history": {"primary": "#D97706", "accent": "#6366F1"},
            "biology": {"primary": "#10B981", "accent": "#3B82F6"},
            "geography": {"primary": "#F59E0B", "accent": "#10B981"}
        }

        # Default theme if subject not recognized
        return themes.get(subject, {"primary": "#6366F1", "accent": "#8B5CF6"})

    def log_generation_start(self, mode: str):
        """Log the start of generation process."""
        logger.info(f"🚀 Starting {mode} HTML generation")
        logger.info(f"🤖 Using AI provider: {self.provider.get_provider_name()}")

    def log_generation_complete(self, duration: float):
        """Log the completion of generation process."""
        logger.info(f"✅ {self.generation_metadata['mode']} generation completed in {duration:.2f}s")
        logger.info(f"📊 Stages completed: {self.generation_metadata['stages_completed']}")
        logger.info(f"🔄 Refinements: {self.generation_metadata['refinements']}")

    def log_error(self, stage: str, error: Exception):
        """Log an error during generation."""
        logger.error(f"❌ Error in {stage}: {str(error)}")
        self._update_generation_info(stage, error=str(error))

    def _sanitize_html_output(self, raw_response: str) -> str:
        """Remove markdown fences and surrounding noise from model HTML output."""
        if not raw_response:
            return ""

        text = raw_response.strip()
        text = re.sub(r"^\s*```\s*[a-zA-Z0-9_-]*\s*\n?", "", text)
        text = re.sub(r"\n?\s*```\s*$", "", text)
        text = text.replace("```html", "").replace("```HTML", "").replace("```", "")
        return text.strip()
