"""
HTML Validator Module

This module provides validation functions for HTML structure and styling.
Used in Heavy Mode generation to ensure quality at each stage.


Date: 2025-01-15
"""

import re
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class HTMLValidator:
    """Validates HTML structure and styling."""

    def validate_structure(self, html: str) -> Tuple[bool, List[str]]:
        """
        Validate HTML structure.

        Args:
            html: HTML string to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check for basic HTML structure
        if not html.strip():
            issues.append("错误：HTML内容为空")
            return False, issues

        # Check for DOCTYPE
        if '<!DOCTYPE html>' not in html:
            issues.append("警告：缺少 <!DOCTYPE html> 声明")

        # Check for html tags
        if '<html' not in html:
            issues.append("错误：缺少 <html> 标签")
        else:
            # Check for lang attribute
            html_tag_match = re.search(r'<html[^>]*lang=["\']([^"\']*)["\']', html)
            if not html_tag_match:
                issues.append("警告：<html> 标签缺少 lang 属性")
            elif html_tag_match.group(1) != 'zh-CN':
                issues.append("警告：lang 属性应该是 'zh-CN'")

        # Check for head and body
        if '<head>' not in html or '</head>' not in html:
            issues.append("错误：缺少 <head> 标签")
        # if '<body>' not in html or '</body>' not in html:
        #     issues.append("错误：缺少 <body> 标签")

        # Check for viewport meta tag (responsive design)
        # if 'viewport' not in html:
        #     issues.append("警告：缺少 viewport meta 标签，影响响应式设计")

        # # Check for charset
        # if 'charset=' not in html:
        #     issues.append("警告：缺少字符集声明")

        # # Check semantic HTML tags
        # semantic_tags = ['<header', '<nav', '<main', '<footer', '<article', '<section']
        # found_semantic = any(tag in html for tag in semantic_tags)
        # if not found_semantic:
        #     issues.append("建议：使用语义化HTML标签（header, nav, main, section等）")

        # Check for closing tags
        open_tags = re.findall(r'<(\w+)[^>]*>', html)
        close_tags = re.findall(r'</(\w+)>', html)
        for tag in set(open_tags):
            if tag not in ['img', 'br', 'hr', 'input', 'meta', 'link']:  # Self-closing tags
                open_count = open_tags.count(tag)
                close_count = close_tags.count(tag)
                if open_count > close_count:
                    issues.append(f"警告：标签 <{tag}> 有 {open_count} 个开始标签但只有 {close_count} 个结束标签")

        is_valid = not any(i.startswith("错误") for i in issues)
        return is_valid, issues

    def validate_styling(self, html: str) -> Tuple[bool, List[str]]:
        """
        Validate CSS styling application.

        Args:
            html: HTML string to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check for CSS presence
        has_css = any(keyword in html for keyword in ['<style', 'class=', 'style='])
        if not has_css:
            issues.append("警告：未检测到CSS样式")
        else:
            # Check for responsive classes
            has_responsive = any(keyword in html for keyword in ['md:', 'lg:', 'sm:', '@media'])
            if not has_responsive:
                issues.append("警告：缺少响应式设计类名或媒体查询")

        # Check for common styling elements
        styling_elements = {
            'rounded': '圆角',
            'shadow': '阴影',
            'bg-': '背景色',
            'text-': '文本颜色',
            'p-': '内边距',
            'm-': '外边距'
        }

        for element, name in styling_elements.items():
            if element not in html:
                issues.append(f"建议：添加{name}样式（{element}）")

        # Check for color consistency
        color_pattern = re.findall(r'#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3}', html)
        if len(color_pattern) > 10:
            issues.append("建议：使用CSS变量统一颜色管理，减少硬编码颜色值")

        # Check for animations
        has_animations = any(keyword in html for keyword in ['animate-', 'transition:', '@keyframes'])
        if not has_animations:
            issues.append("建议：添加过渡动画提升用户体验")

        # Check for loading states
        if 'loading' not in html.lower():
            issues.append("建议：添加加载状态提示")

        is_valid = not any(i.startswith("错误") for i in issues)
        return is_valid, issues

    def validate_responsive(self, html: str) -> Tuple[bool, List[str]]:
        """
        Validate responsive design implementation.

        Args:
            html: HTML string to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check for viewport meta tag
        if 'name="viewport"' not in html and "name='viewport'" not in html:
            issues.append("错误：缺少 viewport meta 标签，无法实现响应式设计")
            return False, issues

        # Check for responsive breakpoints
        breakpoints = ['md:', 'lg:', 'xl:', '2xl:', '@media']
        has_breakpoints = any(bp in html for bp in breakpoints)

        if not has_breakpoints:
            issues.append("警告：未使用响应式断点，在不同屏幕尺寸上显示效果可能不佳")

        # Check for mobile-first classes
        if 'grid-cols-1' not in html and 'flex-col' not in html:
            issues.append("建议：使用移动优先的设计策略（默认单列布局）")

        # Check for touch-friendly targets
        # Buttons should have adequate padding
        button_pattern = re.findall(r'<button[^>]*class=["\']([^"\']*)["\']', html)
        for classes in button_pattern:
            if 'py-' not in classes and 'px-' not in classes:
                issues.append("建议：按钮添加内边距以确保触摸目标足够大（最小44px）")
                break

        # Check for flexible layouts
        has_flex = 'flex' in html
        has_grid = 'grid' in html
        if not (has_flex or has_grid):
            issues.append("建议：使用flex或grid布局实现响应式设计")

        is_valid = not any(i.startswith("错误") for i in issues)
        return is_valid, issues

    def validate_completeness(self, html: str) -> Tuple[bool, List[str]]:
        """
        Validate HTML completeness for Heavy Mode output.

        Args:
            html: HTML string to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check for complete document structure
        required_tags = ['<!DOCTYPE html>', '<html', '</html>', '<head>', '</head>', '<body>', '</body>']
        for tag in required_tags:
            if tag not in html:
                issues.append(f"错误：缺少必需标签 {tag}")

        # Check for content
        body_match = re.search(r'<body>(.*?)</body>', html, re.DOTALL)
        if body_match:
            body_content = body_match.group(1).strip()
            # Remove scripts from content check
            body_content = re.sub(r'<script[^>]*>.*?</script>', '', body_content, flags=re.DOTALL)
            body_content = re.sub(r'<style[^>]*>.*?</style>', '', body_content, flags=re.DOTALL)

            if len(body_content) < 100:
                issues.append("警告：body 内容过少，可能不完整")
        else:
            issues.append("错误：无法找到 body 内容")

        # Check for interactive elements
        has_interactive = any(keyword in html for keyword in ['<button', '<input', '<select', 'onclick=', 'addEventListener'])
        if not has_interactive:
            issues.append("警告：缺少交互元素（按钮、输入框等）")

        # Check for Chinese content
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
        if not chinese_pattern.search(html):
            issues.append("错误：内容未包含中文字符")

        # Check for no placeholder text
        placeholders = ['Lorem ipsum', 'Placeholder', 'TODO', '待添加']
        for placeholder in placeholders:
            if placeholder in html:
                issues.append(f"错误：包含占位符文本 '{placeholder}'")

        is_valid = not any(i.startswith("错误") for i in issues)
        return is_valid, issues

    def validate_complete(self, html: str) -> Tuple[bool, List[str]]:
        """
        Complete validation for Stage 2 output.
        Combines structure, styling, responsive, and completeness checks.

        Args:
            html: HTML string to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        all_issues = []

        # Run all validation checks
        _, structure_issues = self.validate_structure(html)
        _, styling_issues = self.validate_styling(html)
        _, responsive_issues = self.validate_responsive(html)
        _, completeness_issues = self.validate_completeness(html)

        all_issues.extend(structure_issues)
        all_issues.extend(styling_issues)
        all_issues.extend(responsive_issues)
        all_issues.extend(completeness_issues)

        # Additional Stage 2 specific checks

        # Check for left-right layout alignment
        if 'process-panel' not in html and 'simulation-panel' not in html:
            all_issues.append("警告：未找到标准的左右布局面板（process-panel/simulation-panel）")

        # Check for Canvas/SVG presence
        if 'canvas' not in html.lower() and 'svg' not in html.lower():
            all_issues.append("建议：添加Canvas或SVG元素进行可视化模拟")

        # Check for data display panels
        if 'data-panel' not in html and '显示' not in html:
            all_issues.append("建议：添加数据实时显示面板")

        # Check for step indicators
        if 'step' not in html.lower() or '步骤' not in html:
            all_issues.append("建议：添加步骤指示器帮助用户理解流程")

        # Check for visual polish elements
        polish_elements = {
            'rounded-': '圆角',
            'shadow': '阴影',
            'transition': '过渡动画',
            'hover:': '悬停效果'
        }
        for element, name in polish_elements.items():
            if element not in html:
                all_issues.append(f"建议：添加{name}效果提升视觉体验（{element}）")

        # Check for accessibility
        if 'aria-' not in html:
            all_issues.append("建议：添加ARIA标签提升可访问性")

        # Check for error handling in JavaScript
        script_content = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
        if script_content:
            combined_scripts = ' '.join(script_content)
            if 'try' not in combined_scripts and 'catch' not in combined_scripts:
                all_issues.append("建议：在JavaScript中添加try-catch错误处理")

        is_valid = not any(i.startswith("错误") for i in all_issues)
        return is_valid, all_issues

    def get_validation_summary(self, all_validations: Dict[str, Tuple[bool, List[str]]]) -> Dict:
        """
        Get summary of all validations.

        Args:
            all_validations: Dict of {validation_name: (is_valid, issues)}

        Returns:
            Summary dict with overall status and all issues
        """
        all_issues = []
        all_valid = True

        for validation_name, (is_valid, issues) in all_validations.items():
            if not is_valid:
                all_valid = False
            all_issues.extend([f"[{validation_name}] {issue}" for issue in issues])

        return {
            "overall_valid": all_valid,
            "total_issues": len(all_issues),
            "issues": all_issues,
            "validations_performed": list(all_validations.keys())
        }
