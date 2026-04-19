"""
Themes Module

This module provides subject-adaptive color themes for Heavy Mode generation.
Different subjects get different color schemes to match their character.


Date: 2025-01-15
"""

# Subject-adaptive themes
THEMES = {
    "math": {
        "name": "数学",
        "primary": "#3B82F6",      # Blue - precision, logic
        "primary_dark": "#1E40AF",
        "primary_light": "#DBEAFE",
        "accent": "#10B981",       # Green - correctness, solutions
        "accent_dark": "#047857",
        "accent_light": "#D1FAE5",
        "secondary": "#8B5CF6",    # Purple - abstract thinking
        "style": "precise",
        "font": "system-ui, -apple-system, sans-serif",
        "description": "精确、逻辑性强的蓝色主题"
    },
    "physics": {
        "name": "物理",
        "primary": "#8B5CF6",      # Purple - mystery, energy
        "primary_dark": "#5B21B6",
        "primary_light": "#EDE9FE",
        "accent": "#F59E0B",       # Orange - energy, motion
        "accent_dark": "#D97706",
        "accent_light": "#FEF3C7",
        "secondary": "#3B82F6",    # Blue - waves, light
        "style": "experimental",
        "font": "system-ui, -apple-system, sans-serif",
        "description": "探索性、能量感的紫橙配色"
    },
    "chemistry": {
        "name": "化学",
        "primary": "#06B6D4",      # Cyan - liquids, reactions
        "primary_dark": "#0E7490",
        "primary_light": "#CFFAFE",
        "accent": "#EC4899",       # Pink - molecular bonds
        "accent_dark": "#BE185D",
        "accent_light": "#FCE7F3",
        "secondary": "#10B981",    # Green - organic chemistry
        "style": "molecular",
        "font": "system-ui, -apple-system, sans-serif",
        "description": "分子主题的青粉配色"
    },
    "language": {
        "name": "语言",
        "primary": "#EC4899",      # Pink - creativity
        "primary_dark": "#BE185D",
        "primary_light": "#FCE7F3",
        "accent": "#06B6D4",       # Cyan - clarity
        "accent_dark": "#0E7490",
        "accent_light": "#CFFAFE",
        "secondary": "#8B5CF6",    # Purple - imagination
        "style": "creative",
        "font": "Georgia, 'Source Han Serif CN', serif",
        "description": "创意性、文学感的粉青配色"
    },
    "history": {
        "name": "历史",
        "primary": "#D97706",      # Amber - antiquity
        "primary_dark": "#B45309",
        "primary_light": "#FEF3C7",
        "accent": "#6366F1",       # Indigo - legacy
        "accent_dark": "#4338CA",
        "accent_light": "#E0E7FF",
        "secondary": "#78716C",    # Stone - ancient documents
        "style": "narrative",
        "font": "'Source Han Serif CN', 'Noto Serif SC', serif",
        "description": "历史感、叙事性的棕紫配色"
    },
    "biology": {
        "name": "生物",
        "primary": "#10B981",      # Green - nature, life
        "primary_dark": "#047857",
        "primary_light": "#D1FAE5",
        "accent": "#3B82F6",       # Blue - DNA, water
        "accent_dark": "#1E40AF",
        "accent_light": "#DBEAFE",
        "secondary": "#F59E0B",    # Orange - energy, growth
        "style": "organic",
        "font": "system-ui, -apple-system, sans-serif",
        "description": "自然、生命力的绿色主题"
    },
    "geography": {
        "name": "地理",
        "primary": "#F59E0B",      # Amber - earth
        "primary_dark": "#D97706",
        "primary_light": "#FEF3C7",
        "accent": "#10B981",       # Green - land, vegetation
        "accent_dark": "#047857",
        "accent_light": "#D1FAE5",
        "secondary": "#3B82F6",    # Blue - oceans, sky
        "style": "exploratory",
        "font": "system-ui, -apple-system, sans-serif",
        "description": "探索性、地球感的棕绿蓝配色"
    },
    "computer_science": {
        "name": "计算机科学",
        "primary": "#6366F1",      # Indigo - technology
        "primary_dark": "#4338CA",
        "primary_light": "#E0E7FF",
        "accent": "#10B981",       # Green - code, success
        "accent_dark": "#047857",
        "accent_light": "#D1FAE5",
        "secondary": "#8B5CF6",    # Purple - innovation
        "style": "modern",
        "font": "'JetBrains Mono', 'Fira Code', monospace",
        "description": "现代科技感的靛绿配色"
    },
    "default": {
        "name": "通用",
        "primary": "#6366F1",      # Indigo
        "primary_dark": "#4338CA",
        "primary_light": "#E0E7FF",
        "accent": "#8B5CF6",       # Purple
        "accent_dark": "#5B21B6",
        "accent_light": "#EDE9FE",
        "secondary": "#10B981",    # Green
        "style": "balanced",
        "font": "system-ui, -apple-system, sans-serif",
        "description": "平衡通用的靛紫配色"
    }
}

def get_theme(subject_area: str) -> dict:
    """
    Get theme for a subject area.

    Args:
        subject_area: Subject name (e.g., "math", "physics", "化学")

    Returns:
        Theme dictionary with colors and styling
    """
    subject_lower = subject_area.lower()

    # Direct match
    if subject_lower in THEMES:
        return THEMES[subject_lower]

    # Partial match for Chinese subject names
    for key, theme in THEMES.items():
        if key in subject_lower or subject_lower in key:
            return theme

    # Fallback to default
    return THEMES["default"]

# CSS custom properties generation
def generate_theme_css(theme: dict) -> str:
    """
    Generate CSS custom properties from theme.

    Args:
        theme: Theme dictionary

    Returns:
        CSS string with custom properties
    """
    return f"""
:root {{
    --color-primary: {theme['primary']};
    --color-primary-dark: {theme['primary_dark']};
    --color-primary-light: {theme['primary_light']};
    --color-accent: {theme['accent']};
    --color-accent-dark: {theme['accent_dark']};
    --color-accent-light: {theme['accent_light']};
    --color-secondary: {theme['secondary']};
    --font-family: {theme['font']};
}}

/* Component-specific variables */
.bg-primary {{ background-color: var(--color-primary); }}
.bg-primary-light {{ background-color: var(--color-primary-light); }}
.text-primary {{ color: var(--color-primary); }}
.border-primary {{ border-color: var(--color-primary); }}

.bg-accent {{ background-color: var(--color-accent); }}
.bg-accent-light {{ background-color: var(--color-accent-light); }}
.text-accent {{ color: var(--color-accent); }}
.border-accent {{ border-color: var(--color-accent); }}
"""

# Gradient combinations for visual appeal
# Note: These are templates - use .format() with actual color values
GRADIENTS = {
    "hero": "from-{primary}-50 to-{accent}-50",
    "card": "from-white to-{primary_light}",
    "button": "from-{primary} to-{primary_dark}",
    "section": "from-{primary_light}-30 to-white",
    "footer": "from-gray-50 to-gray-100"
}

def get_gradient(gradient_type: str, theme: dict) -> str:
    """
    Get a formatted gradient string for a theme.

    Args:
        gradient_type: Type of gradient ('hero', 'card', 'button', 'section', 'footer')
        theme: Theme dictionary with color keys

    Returns:
        Formatted gradient string for Tailwind CSS
    """
    template = GRADIENTS.get(gradient_type, "")
    if not template:
        return ""

    return template.format(
        primary=theme['primary'].replace('#', ''),
        accent=theme['accent'].replace('#', ''),
        primary_light=theme['primary_light'].replace('#', ''),
        primary_dark=theme['primary_dark'].replace('#', '')
    )

# Duolingo-inspired color tokens for quick reference
DUOLINGO_COLORS = {
    "green": "#58CC02",
    "green_dark": "#58A700",
    "green_light": "#89E219",
    "blue": "#1CB0F6",
    "blue_dark": "#1899D6",
    "blue_light": "#4DC8FC",
    "red": "#FF4B4B",
    "red_dark": "#EA2B2B",
    "yellow": "#FFC800",
    "yellow_dark": "#E5B800",
    "purple": "#CE82FF",
    "purple_dark": "#A568CC",
    "gray": "#E5E5E5",
    "gray_dark": "#AFB2C3"
}
