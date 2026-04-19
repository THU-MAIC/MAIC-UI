"""
Visual Components Module

This module provides pre-built visual component templates for Heavy Mode generation.
These components implement Duolingo-inspired design with rounded corners, playful colors,
and smooth animations.


Date: 2025-01-15
"""

VISUAL_COMPONENTS = {
    "RoundedCard": {
        "name": "RoundedCard",
        "category": "visual",
        "description": "White cards with soft shadows and rounded corners (border-radius-2xl)",
        "template": """
<div class="rounded-card bg-white rounded-2xl shadow-md hover:shadow-lg transition-shadow duration-300 p-6 {extra_classes}">
    {card_content}
</div>
""",
        "variants": {
            "default": "rounded-2xl shadow-md",
            "elevated": "rounded-2xl shadow-lg",
            "bordered": "rounded-2xl shadow-md border-2 border-{primary_color}-200",
            "gradient": "rounded-2xl shadow-md bg-gradient-to-br from-{primary_color}-50 to-white"
        },
        "props": {
            "content": "HTML content",
            "variant": "default | elevated | bordered | gradient",
            "primary_color": "color",
            "extra_classes": "additional CSS classes"
        }
    },

    "PlayfulButton": {
        "name": "PlayfulButton",
        "category": "visual",
        "description": "Pill-shaped buttons with hover bounce animation",
        "template": """
<button class="playful-button px-6 py-3 bg-{primary_color}-500 text-white font-semibold rounded-full
                    hover:bg-{primary_color}-600 hover:scale-105 active:scale-95
                    transition-all duration-200 shadow-md hover:shadow-lg
                    {extra_classes}">
    {button_content}
</button>
""",
        "variants": {
            "primary": "bg-{primary_color}-500 hover:bg-{primary_color}-600",
            "secondary": "bg-gray-200 text-gray-700 hover:bg-gray-300",
            "success": "bg-green-500 hover:bg-green-600",
            "warning": "bg-yellow-500 hover:bg-yellow-600",
            "danger": "bg-red-500 hover:bg-red-600"
        },
        "props": {
            "content": "text or HTML",
            "variant": "primary | secondary | success | warning | danger",
            "primary_color": "color",
            "disabled": "boolean"
        },
        "chinese_labels": {
            "submit": "提交",
            "continue": "继续",
            "next": "下一题",
            "previous": "上一题",
            "check": "检查答案",
            "skip": "跳过",
            "retry": "重试"
        }
    },

    "EmojiBadge": {
        "name": "EmojiBadge",
        "category": "visual",
        "description": "Large emoji icons for achievements and feedback",
        "template": """
<div class="emoji-badge text-center {extra_classes}">
    <div class="emoji-icon text-6xl mb-3 animate-bounce">{emoji}</div>
    <div class="badge-title text-xl font-bold text-gray-800">{title}</div>
    {description}
</div>
""",
        "emoji_sets": {
            "achievement": ["🏆", "⭐", "🎯", "🌟", "💫", "🔥"],
            "success": ["✅", "🎉", "👏", "🙌", "💪", "🚀"],
            "encouragement": ["💪", "🤔", "🔍", "💡", "📚", "✨"],
            "progress": ["📈", "🎯", "⏳", "🔄", "➡️", "✅"]
        },
        "props": {
            "emoji": "emoji character",
            "title": "string",
            "description": "HTML (optional)",
            "extra_classes": "additional CSS classes"
        }
    },

    "ConfettiCanvas": {
        "name": "ConfettiCanvas",
        "category": "visual",
        "description": "Celebration animations on completion",
        "template": """
<canvas id="confettiCanvas" class="confetti-canvas fixed inset-0 pointer-events-none z-50"></canvas>
<script>
class Confetti {{
    constructor() {{
        this.canvas = document.getElementById('confettiCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];
        this.resize();
        window.addEventListener('resize', () => this.resize());
    }}

    resize() {{
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }}

    createParticle(x, y) {{
        return {{
            x: x,
            y: y,
            size: Math.random() * 10 + 5,
            color: this.colors[Math.floor(Math.random() * this.colors.length)],
            speedX: Math.random() * 6 - 3,
            speedY: Math.random() * -10 - 5,
            gravity: 0.2,
            rotation: Math.random() * 360,
            rotationSpeed: Math.random() * 10 - 5
        }};
    }}

    explode(x, y) {{
        for (let i = 0; i < 100; i++) {{
            this.particles.push(this.createParticle(x, y));
        }}
    }}

    update() {{
        this.particles.forEach((p, i) => {{
            p.x += p.speedX;
            p.y += p.speedY;
            p.speedY += p.gravity;
            p.rotation += p.rotationSpeed;

            if (p.y > this.canvas.height + 50) {{
                this.particles.splice(i, 1);
            }}
        }});
    }}

    draw() {{
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.particles.forEach(p => {{
            this.ctx.save();
            this.ctx.translate(p.x, p.y);
            this.ctx.rotate((p.rotation * Math.PI) / 180);
            this.ctx.fillStyle = p.color;
            this.ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
            this.ctx.restore();
        }});
    }}

    animate() {{
        this.update();
        this.draw();
        if (this.particles.length > 0) {{
            requestAnimationFrame(() => this.animate());
        }}
    }}

    celebrate() {{
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        this.explode(centerX, centerY);
        this.explode(centerX - 200, centerY - 100);
        this.explode(centerX + 200, centerY - 100);
        this.animate();
    }}
}}

// Usage: new Confetti().celebrate();
</script>
""",
        "props": {
            "trigger": "event trigger"
        }
    },

    "ProgressCharacter": {
        "name": "ProgressCharacter",
        "category": "visual",
        "description": "Animated mascot for progress tracking (optional)",
        "template": """
<div class="progress-character fixed bottom-4 right-4 z-40 {hidden_class}">
    <div class="character-container">
        <div class="character-bubble bg-white rounded-2xl shadow-lg p-4 mb-2 max-w-xs">
            <div class="bubble-text font-medium text-gray-800">{message}</div>
            <div class="bubble-tail absolute bottom-0 right-8 w-4 h-4 bg-white transform rotate-45 translate-y-2"></div>
        </div>
        <div class="character-avatar text-6xl animate-bounce">
            {avatar}
        </div>
    </div>
</div>
""",
        "avatars": {
            "owl": "🦉",
            "cat": "🐱",
            "dog": "🐕",
            "robot": "🤖",
            "alien": "👽",
            "ghost": "👻"
        },
        "messages": {
            "encouragement": ["加油！", "继续努力！", "你可以的！", "做得好！"],
            "hint": ["需要提示吗？", "试试仔细观察", "记住关键概念"],
            "celebration": ["太棒了！", "完美！", "你真厉害！", "继续加油！"]
        }
    }
}

# Animation presets
ANIMATION_PRESETS = {
    "bounce": """
@keyframes bounce {{
    0%, 100% {{ transform: translateY(0); }}
    50% {{ transform: translateY(-10px); }}
}}
.animate-bounce {{ animation: bounce 1s infinite; }}
""",
    "pulse": """
@keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.5; }}
}}
.animate-pulse {{ animation: pulse 2s infinite; }}
""",
    "shake": """
@keyframes shake {{
    0%, 100% {{ transform: translateX(0); }}
    25% {{ transform: translateX(-5px); }}
    75% {{ transform: translateX(5px); }}
}}
.animate-shake {{ animation: shake 0.5s; }}
""",
    "slideIn": """
@keyframes slideIn {{
    from {{ transform: translateX(-100%); opacity: 0; }}
    to {{ transform: translateX(0); opacity: 1; }}
}}
.animate-slide-in {{ animation: slideIn 0.5s ease-out; }}
""",
    "fadeIn": """
@keyframes fadeIn {{
    from {{ opacity: 0; }}
    to {{ opacity: 1; }}
}}
.animate-fade-in {{ animation: fadeIn 0.3s ease-in; }}
"""
}

# Spacing scale (Duolingo-inspired)
SPACING_SCALE = {
    "xs": "0.25rem (4px)",
    "sm": "0.5rem (8px)",
    "md": "1rem (16px)",
    "lg": "1.5rem (24px)",
    "xl": "2rem (32px)",
    "2xl": "3rem (48px)",
    "3xl": "4rem (64px)"
}

# Border radius scale
BORDER_RADIUS = {
    "sm": "0.25rem (4px)",
    "md": "0.5rem (8px)",
    "lg": "0.75rem (12px)",
    "xl": "1rem (16px)",
    "2xl": "1.5rem (24px)",
    "3xl": "2rem (32px)",
    "full": "9999px (pill)"
}

# Shadow scale
SHADOW_SCALE = {
    "sm": "0 1px 2px rgba(0,0,0,0.05)",
    "md": "0 4px 6px rgba(0,0,0,0.1)",
    "lg": "0 10px 15px rgba(0,0,0,0.1)",
    "xl": "0 20px 25px rgba(0,0,0,0.15)"
}

# Color palette suggestions
COLOR_PALETTES = {
    "duolingo": {
        "primary": "#58CC02",  # Green
        "secondary": "#1CB0F6",  # Blue
        "accent": "#FFC800",  # Yellow
        "danger": "#FF4B4B",  # Red
        "neutral": "#E5E5E5"  # Gray
    },
    "playful_learning": {
        "primary": "#3B82F6",  # Blue
        "secondary": "#10B981",  # Green
        "accent": "#F59E0B",  # Orange
        "danger": "#EF4444",  # Red
        "neutral": "#F3F4F6"  # Gray
    },
    "nature": {
        "primary": "#059669",  # Emerald
        "secondary": "#0D9488",  # Teal
        "accent": "#FBBF24",  # Amber
        "danger": "#DC2626",  # Red
        "neutral": "#ECFDF5"  # Light green
    }
}

# Typography hierarchy (Chinese-optimized)
TYPOGRAPHY_SCALE = {
    "display": {
        "size": "4.5rem (72px)",
        "weight": "800",
        "line_height": "1.1",
        "usage": "Hero titles"
    },
    "h1": {
        "size": "3rem (48px)",
        "weight": "700",
        "line_height": "1.2",
        "usage": "Page titles"
    },
    "h2": {
        "size": "2.25rem (36px)",
        "weight": "600",
        "line_height": "1.3",
        "usage": "Section headers"
    },
    "h3": {
        "size": "1.875rem (30px)",
        "weight": "600",
        "line_height": "1.4",
        "usage": "Subsection headers"
    },
    "body_large": {
        "size": "1.125rem (18px)",
        "weight": "400",
        "line_height": "1.7",
        "usage": "Lead paragraphs"
    },
    "body": {
        "size": "1rem (16px)",
        "weight": "400",
        "line_height": "1.7",
        "usage": "Body text (Chinese-optimized)"
    },
    "body_small": {
        "size": "0.875rem (14px)",
        "weight": "400",
        "line_height": "1.6",
        "usage": "Secondary text"
    },
    "caption": {
        "size": "0.75rem (12px)",
        "weight": "400",
        "line_height": "1.5",
        "usage": "Captions, labels"
    }
}
