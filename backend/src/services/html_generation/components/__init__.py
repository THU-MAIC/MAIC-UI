"""
HTML Generation Components Package

This package provides pre-built component templates for Heavy Mode generation.
Components are organized by category: layout, interactive, visual, and themes.


Date: 2025-01-15
"""

from .layout_components import LAYOUT_COMPONENTS, LAYOUT_PATTERNS, RESPONSIVE_GUIDANCE
from .interactive_components import (
    INTERACTIVE_COMPONENTS,
    PHYSICS_CONSTRAINTS,
    BLOOMS_LEVELS
)
from .visual_components import (
    VISUAL_COMPONENTS,
    ANIMATION_PRESETS,
    SPACING_SCALE,
    BORDER_RADIUS,
    SHADOW_SCALE,
    COLOR_PALETTES,
    TYPOGRAPHY_SCALE
)
from .themes import THEMES, get_theme, generate_theme_css, GRADIENTS, DUOLINGO_COLORS

# Combine all components for easy reference
ALL_COMPONENTS = {
    "layout": LAYOUT_COMPONENTS,
    "interactive": INTERACTIVE_COMPONENTS,
    "visual": VISUAL_COMPONENTS
}

__all__ = [
    # Layout
    'LAYOUT_COMPONENTS',
    'LAYOUT_PATTERNS',
    'RESPONSIVE_GUIDANCE',

    # Interactive
    'INTERACTIVE_COMPONENTS',
    'PHYSICS_CONSTRAINTS',
    'BLOOMS_LEVELS',

    # Visual
    'VISUAL_COMPONENTS',
    'ANIMATION_PRESETS',
    'SPACING_SCALE',
    'BORDER_RADIUS',
    'SHADOW_SCALE',
    'COLOR_PALETTES',
    'TYPOGRAPHY_SCALE',

    # Themes
    'THEMES',
    'get_theme',
    'generate_theme_css',
    'GRADIENTS',
    'DUOLINGO_COLORS',

    # Combined
    'ALL_COMPONENTS'
]
