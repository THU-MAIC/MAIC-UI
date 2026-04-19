"""
Templates Package

This package contains prompt templates for HTML generation.

Date: 2025-01-15
"""

from .heavy_mode_prompts import (
    get_stage_prompt,
    get_refinement_prompt,
    LANGUAGE_REQUIREMENTS,
    STAGE1_ALIGNED_SIMULATION_PROMPT,
    STAGE2_POLISH_PROMPT,
    REFINEMENT_PROMPTS
)

__all__ = [
    'get_stage_prompt',
    'get_refinement_prompt',
    'LANGUAGE_REQUIREMENTS',
    'STAGE1_ALIGNED_SIMULATION_PROMPT',
    'STAGE2_POLISH_PROMPT',
    'REFINEMENT_PROMPTS'
]
