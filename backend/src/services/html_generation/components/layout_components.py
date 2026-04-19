"""
Layout Components Module

This module provides pre-built layout component templates for Heavy Mode generation.
These components are referenced by the AI during the structure & layout stage.


Date: 2025-01-15
"""

# Layout component templates with Chinese labels
LAYOUT_COMPONENTS = {
    "HeroSection": {
        "name": "HeroSection",
        "category": "layout",
        "description": "Large welcoming header with progress indicator",
        "template": """
<div class="hero-section bg-gradient-to-br from-{primary_color}-50 to-{accent_color}-50 rounded-2xl p-8 mb-8 shadow-lg">
    <div class="max-w-4xl mx-auto text-center">
        <h1 class="text-4xl md:text-5xl font-bold text-gray-800 mb-4">{title}</h1>
        <p class="text-lg text-gray-600 mb-6">{subtitle}</p>
        <div class="flex items-center justify-center gap-4">
            <div class="w-full bg-gray-200 rounded-full h-3">
                <div class="bg-{primary_color}-600 h-3 rounded-full transition-all duration-500" style="width: {progress}%"></div>
            </div>
            <span class="text-sm font-semibold text-{primary_color}-600">{progress}%</span>
        </div>
    </div>
</div>
""",
        "props": {
            "title": "string",
            "subtitle": "string",
            "progress": "number (0-100)",
            "primary_color": "color",
            "accent_color": "color"
        },
        "chinese_labels": {
            "title": "学习标题",
            "subtitle": "学习描述",
            "progress": "学习进度"
        }
    },

    "TwoColumnLayout": {
        "name": "TwoColumnLayout",
        "category": "layout",
        "description": "Content left, interactive simulation right",
        "template": """
<div class="two-column-layout grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
    <div class="content-column bg-white rounded-2xl shadow-md p-6">
        <h2 class="text-2xl font-bold text-gray-800 mb-4">{content_title}</h2>
        <div class="prose prose-lg max-w-none">
            {content_body}
        </div>
    </div>
    <div class="interactive-column bg-gradient-to-br from-{primary_color}-50 to-white rounded-2xl shadow-md p-6">
        <h3 class="text-xl font-semibold text-{primary_color}-700 mb-4">{simulation_title}</h3>
        <div class="simulation-container bg-white rounded-xl p-4 shadow-inner">
            {simulation_content}
        </div>
    </div>
</div>
""",
        "props": {
            "content_title": "string",
            "content_body": "HTML content",
            "simulation_title": "string",
            "simulation_content": "HTML content",
            "primary_color": "color"
        },
        "chinese_labels": {
            "content_title": "学习内容",
            "simulation_title": "互动实验"
        }
    },

    "CardGrid": {
        "name": "CardGrid",
        "category": "layout",
        "description": "Responsive grid for concepts/vocabulary",
        "template": """
<div class="card-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
    {cards}
</div>
<!-- Single card template -->
<div class="concept-card bg-white rounded-2xl shadow-md hover:shadow-lg transition-shadow duration-300 p-6 border-t-4 border-{primary_color}-500">
    <div class="card-icon text-4xl mb-4">{icon}</div>
    <h3 class="text-xl font-bold text-gray-800 mb-2">{title}</h3>
    <p class="text-gray-600 mb-4">{description}</p>
    <button class="w-full bg-{primary_color}-500 text-white py-2 px-4 rounded-xl hover:bg-{primary_color}-600 transition-colors duration-200">
        {button_text}
    </button>
</div>
""",
        "props": {
            "cards": "array of card objects",
            "primary_color": "color"
        },
        "chinese_labels": {
            "button_text": "了解更多"
        }
    },

    "StepWizard": {
        "name": "StepWizard",
        "category": "layout",
        "description": "Sequential learning path with checkpoints",
        "template": """
<div class="step-wizard mb-8">
    <div class="steps-container">
        <div class="flex items-center justify-between mb-8">
            {steps}
        </div>
        <!-- Single step -->
        <div class="step flex-1 flex flex-col items-center">
            <div class="step-circle w-12 h-12 rounded-full bg-{primary_color}-500 text-white flex items-center justify-center font-bold text-lg mb-2 shadow-md">
                {step_number}
            </div>
            <div class="step-title text-sm font-semibold text-gray-700 text-center">{step_title}</div>
            <div class="step-desc text-xs text-gray-500 text-center mt-1">{step_description}</div>
        </div>
    </div>
    <div class="step-content bg-white rounded-2xl shadow-md p-8">
        <h3 class="text-2xl font-bold text-gray-800 mb-4">{current_step_title}</h3>
        <div class="prose max-w-none">{current_step_content}</div>
        <div class="step-navigation flex justify-between mt-8">
            <button class="px-6 py-3 bg-gray-200 text-gray-700 rounded-xl hover:bg-gray-300 transition-colors duration-200" {prev_disabled}>
                ← 上一步
            </button>
            <button class="px-6 py-3 bg-{primary_color}-500 text-white rounded-xl hover:bg-{primary_color}-600 transition-colors duration-200">
                下一步 →
            </button>
        </div>
    </div>
</div>
""",
        "props": {
            "steps": "array of step objects",
            "current_step": "number",
            "primary_color": "color"
        },
        "chinese_labels": {
            "prev_button": "上一步",
            "next_button": "下一步"
        }
    },

    "ProgressBar": {
        "name": "ProgressBar",
        "category": "layout",
        "description": "Animated progress with milestone markers",
        "template": """
<div class="progress-bar-container mb-8">
    <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-semibold text-gray-700">{title}</span>
        <span class="text-sm font-bold text-{primary_color}-600">{progress}%</span>
    </div>
    <div class="relative">
        <div class="w-full bg-gray-200 rounded-full h-4 shadow-inner">
            <div class="bg-gradient-to-r from-{primary_color}-500 to-{accent_color}-500 h-4 rounded-full transition-all duration-500 shadow-md"
                 style="width: {progress}%"></div>
        </div>
        <!-- Milestone markers -->
        <div class="absolute top-0 left-0 w-full flex justify-between px-1">
            {milestones}
        </div>
        <!-- Single milestone -->
        <div class="milestone w-3 h-3 rounded-full bg-white border-2 border-{primary_color}-500 transform -translate-y-0.5"
             style="left: {position}%"></div>
    </div>
    <div class="flex justify-between mt-2 text-xs text-gray-500">
        <span>开始</span>
        {milestone_labels}
        <span>完成</span>
    </div>
</div>
""",
        "props": {
            "title": "string",
            "progress": "number (0-100)",
            "milestones": "array of milestone positions",
            "primary_color": "color",
            "accent_color": "color"
        },
        "chinese_labels": {
            "start": "开始",
            "complete": "完成"
        }
    }
}

# Layout patterns for different content types
LAYOUT_PATTERNS = {
    "procedural_knowledge": "TwoColumnLayout",
    "vocabulary_list": "CardGrid",
    "sequential_learning": "StepWizard",
    "overview": "HeroSection",
    "progress_tracking": "ProgressBar"
}

# Responsive breakpoints guidance
RESPONSIVE_GUIDANCE = """
响应式设计断点（Responsive Breakpoints）：
- 移动设备（Mobile）: < 768px - 单列布局，较大触摸目标
- 平板设备（Tablet）: 768px - 1023px - 两列布局，适中间距
- 桌面设备（Desktop）: ≥ 1024px - 多列布局，充分利用空间

移动优先原则（Mobile First）：
1. 默认样式为移动设备
2. 使用 media query (min-width: 768px) 添加平板样式
3. 使用 media query (min-width: 1024px) 添加桌面样式

触摸目标尺寸要求：
- 按钮、链接最小尺寸: 44px × 44px
- 交互元素间距: 至少 8px
"""
