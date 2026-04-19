"""
Unit Tests for HTML Generation Validators

Tests for HTMLValidator, ContentValidator, and SimulationValidator.

Date: 2025-01-15
"""

import pytest
import sys
import os

# Add project root to path
sys.path.append('.')

from src.services.validators import HTMLValidator, ContentValidator, SimulationValidator


class TestHTMLValidator:
    """Test HTML validation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = HTMLValidator()

    def test_validate_complete_html(self):
        """Test validation of complete, valid HTML."""
        html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试</title>
</head>
<body>
    <header>头部</header>
    <main>内容</main>
    <footer>底部</footer>
</body>
</html>"""
        is_valid, issues = self.validator.validate_structure(html)
        assert is_valid
        assert len([i for i in issues if i.startswith("错误")]) == 0
        print("✅ Complete HTML validation passed")

    def test_validate_missing_doctype(self):
        """Test detection of missing DOCTYPE."""
        html = """<html lang="zh-CN">
<head><meta charset="UTF-8"></head>
<body>内容</body>
</html>"""
        is_valid, issues = self.validator.validate_structure(html)
        assert not is_valid
        assert any("DOCTYPE" in issue for issue in issues)
        print("✅ Missing DOCTYPE detected")

    def test_validate_chinese_lang_attribute(self):
        """Test Chinese lang attribute validation."""
        html = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"></head>
<body>内容</body>
</html>"""
        is_valid, issues = self.validator.validate_structure(html)
        assert any("zh-CN" in issue for issue in issues)
        print("✅ Chinese lang attribute validation works")

    def test_validate_responsive_breakpoints(self):
        """Test responsive design breakpoint validation."""
        html_no_responsive = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"></head>
<body>
    <div style="width: 1000px;">固定宽度</div>
</body>
</html>"""
        is_valid, issues = self.validator.validate_responsive(html_no_responsive)
        assert not is_valid
        assert any("响应式" in issue or "responsive" in issue.lower() for issue in issues)
        print("✅ Responsive breakpoint validation works")

    def test_validate_with_responsive_classes(self):
        """Test HTML with Tailwind responsive classes."""
        html_responsive = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"></head>
<body>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        <div class="p-4 md:p-6">响应式内容</div>
    </div>
</body>
</html>"""
        is_valid, issues = self.validator.validate_responsive(html_responsive)
        assert is_valid
        print("✅ Responsive classes validation passed")


class TestContentValidator:
    """Test content validation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ContentValidator()

    def test_validate_chinese_content(self):
        """Test Chinese language validation."""
        html_chinese = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; line-height: 1.7; }}
    </style>
</head>
<body>
    <h1>中文标题</h1>
    <p>这是中文内容，包含足够的中文字符。</p>
</body>
</html>"""
        is_valid, issues = self.validator.validate_chinese(html_chinese)
        assert is_valid
        print("✅ Chinese content validation passed")

    def test_detect_english_placeholder(self):
        """Test detection of English placeholders."""
        html_with_placeholder = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"></head>
<body>
    <p>Placeholder text here</p>
</body>
</html>"""
        is_valid, issues = self.validator.validate_chinese(html_with_placeholder)
        assert not is_valid
        assert any("Placeholder" in issue or "占位符" in issue for issue in issues)
        print("✅ English placeholder detected")

    def test_validate_content_completeness(self):
        """Test content completeness validation."""
        analysis = {
            'key_concepts': ['概念一', '概念二', '概念三'],
            'main_topics': ['主题一']
        }
        html_complete = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"></head>
<body>
    <h1>概念一</h1>
    <p>概念一的详细说明</p>
    <h2>概念二</h2>
    <p>概念二的详细说明</p>
    <h3>主题一</h3>
    <p>主题一的详细说明</p>
</body>
</html>"""
        is_valid, issues = self.validator.validate_content_completeness(html_complete, analysis)
        assert is_valid
        print("✅ Content completeness validation passed")

    def test_detect_missing_concepts(self):
        """Test detection of missing key concepts."""
        analysis = {
            'key_concepts': ['概念一', '概念二', '概念三'],
            'main_topics': []
        }
        html_incomplete = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"></head>
<body>
    <h1>概念一</h1>
    <p>只有概念一的内容</p>
</body>
</html>"""
        is_valid, issues = self.validator.validate_content_completeness(html_incomplete, analysis)
        assert not is_valid
        assert any("概念二" in issue or "概念三" in issue for issue in issues)
        print("✅ Missing concepts detected")

    def test_validate_interactive_elements(self):
        """Test interactive elements validation."""
        html_with_interactive = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"></head>
<body>
    <button id="startBtn">开始实验</button>
    <button id="resetBtn">重置</button>
    <script>
        document.getElementById('startBtn').addEventListener('click', start);
    </script>
</body>
</html>"""
        is_valid, issues = self.validator.validate_interactive_elements(html_with_interactive)
        assert is_valid
        print("✅ Interactive elements validation passed")


class TestSimulationValidator:
    """Test simulation validation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SimulationValidator()

    def test_validate_pendulum_physics(self):
        """Test pendulum physics validation."""
        valid_pendulum = """
        const g = 9.8;
        const length = 100;
        const period = 2 * Math.PI * Math.sqrt(length / g);
        """
        is_valid, issues = self.validator.validate_physics(valid_pendulum, "pendulum")
        assert is_valid
        print("✅ Valid pendulum physics passed")

    def test_detect_missing_gravity(self):
        """Test detection of missing gravity in pendulum."""
        invalid_pendulum = """
        const length = 100;
        const period = 2 * Math.PI * Math.sqrt(length);
        """
        is_valid, issues = self.validator.validate_physics(invalid_pendulum, "pendulum")
        assert not is_valid
        assert any("gravity" in issue.lower() or "重力" in issue for issue in issues)
        print("✅ Missing gravity detected")

    def test_validate_projectile_motion(self):
        """Test projectile motion validation."""
        valid_projectile = """
        const v0 = 50;
        const angle = 45;
        const g = 9.8;
        const vx = v0 * Math.cos(angle * Math.PI / 180);
        const vy = v0 * Math.sin(angle * Math.PI / 180);
        """
        is_valid, issues = self.validator.validate_physics(valid_projectile, "projectile")
        assert is_valid
        print("✅ Valid projectile motion passed")

    def test_validate_interactive_functionality(self):
        """Test interactive functionality validation."""
        html_complete = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"></head>
<body>
    <canvas id="simCanvas" width="400" height="300"></canvas>
    <button id="startBtn">开始</button>
    <button id="resetBtn">重置</button>
    <script>
        function animate() {{
            requestAnimationFrame(animate);
        }}
        document.getElementById('startBtn').addEventListener('click', animate);
    </script>
</body>
</html>"""
        is_valid, issues = self.validator.validate_interactive_functionality(html_complete)
        assert is_valid
        print("✅ Interactive functionality validation passed")

    def test_detect_missing_canvas(self):
        """Test detection of missing canvas element."""
        html_no_canvas = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"></head>
<body>
    <button>开始</button>
</body>
</html>"""
        is_valid, issues = self.validator.validate_interactive_functionality(html_no_canvas)
        assert not is_valid
        assert any("canvas" in issue.lower() for issue in issues)
        print("✅ Missing canvas detected")


class TestValidationSummary:
    """Test validation summary generation."""

    def test_html_validator_summary(self):
        """Test HTML validator summary."""
        validator = HTMLValidator()
        html = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"></head>
<body>内容</body>
</html>"""

        all_validations = {
            'structure': validator.validate_structure(html),
            'styling': validator.validate_styling(html),
            'responsive': validator.validate_responsive(html)
        }

        summary = validator.get_validation_summary(all_validations)
        assert 'overall_valid' in summary
        assert 'total_issues' in summary
        assert 'issues' in summary
        assert 'validations_performed' in summary
        print(f"✅ HTML validator summary: {summary['total_issues']} issues")

    def test_content_validator_all(self):
        """Test complete content validation."""
        validator = ContentValidator()
        html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <style>body { font-family: 'Microsoft YaHei'; }</style>
</head>
<body>
    <h1>概念</h1>
    <p>内容说明</p>
    <button>按钮</button>
</body>
</html>"""

        analysis = {
            'key_concepts': ['概念'],
            'main_topics': []
        }
        user_preferences = {'grade_level': 6}

        result = validator.validate_all(html, analysis, user_preferences)
        assert 'overall_valid' in result
        assert 'details' in result
        print(f"✅ Content validator all: {result['total_issues']} issues")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
