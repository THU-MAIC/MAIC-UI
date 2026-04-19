"""
HTML Generation Package

This package provides HTML generation with two modes:
- Fast Mode: One-shot generation (~30 seconds)
- Heavy Mode: 4-stage pipeline with validation (~3-5 minutes)

Date: 2025-01-15
"""

from .base_generator import BaseGenerator
from .fast_generator import FastGenerator
from .heavy_generator import HeavyGenerator
from .components import THEMES, get_theme
from .cache import get_cache, GenerationCache

__all__ = [
    'BaseGenerator',
    'FastGenerator',
    'HeavyGenerator',
    'THEMES',
    'get_theme',
    'get_cache',
    'GenerationCache'
]
