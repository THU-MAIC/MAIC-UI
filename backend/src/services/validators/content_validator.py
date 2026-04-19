"""
Content Validator Module

This module provides validation functions for content completeness and Chinese language.
Used in Heavy Mode generation Stage 2 (Content Injection).


Date: 2025-01-15
"""

import re
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class ContentValidator:
    """Validates content completeness and Chinese language usage."""

    def __init__(self):
        """Initialize the content validator."""
        self.chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
        self.english_placeholder_pattern = re.compile(
            r'(Lorem ipsum|Placeholder|Enter text here|TODO|待添加|Click here)',
            re.IGNORECASE
        )

    def validate_chinese(self, html: str) -> Tuple[bool, List[str]]:
        """
        Validate that content is in Chinese.

        Args:
            html: HTML string to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check for Chinese characters
        chinese_matches = self.chinese_pattern.findall(html)
        if not chinese_matches:
            issues.append("错误：HTML内容似乎不包含中文字符")
            return False, issues

        chinese_ratio = len(chinese_matches) / (len(html) - len(re.findall(r'<[^>]+>', html)))

        if chinese_ratio < 0.1:
            issues.append("警告：中文字符比例过低（<10%），可能未完全翻译")

        # Check for Chinese font support
        if "font-family" not in html:
            issues.append("建议：未指定中文字体，可能影响显示效果")
        else:
            # Check for common Chinese fonts
            chinese_fonts = ['Microsoft YaHei', 'SimHei', 'Source Han Sans', 'Noto Sans CJK', 'PingFang']
            has_chinese_font = any(font in html for font in chinese_fonts)
            if not has_chinese_font:
                issues.append("建议：添加中文字体（如 'Microsoft YaHei', 'Source Han Sans CN'）")

        # Check for Chinese-friendly line height
        if 'line-height' not in html:
            issues.append("建议：中文内容的行高应设置为1.6-1.8以提升可读性")

        # Check for English placeholders
        placeholders = self.english_placeholder_pattern.findall(html)
        if placeholders:
            for placeholder in set(placeholders):
                issues.append(f"错误：发现英文占位符 '{placeholder}'，应替换为中文")

        # Check for common English UI text
        english_ui_terms = {
            'Submit': '提交',
            'Continue': '继续',
            'Next': '下一步',
            'Previous': '上一题',
            'Check': '检查',
            'Start': '开始',
            'Reset': '重置'
        }

        for en, zh in english_ui_terms.items():
            # Check for English term outside of code blocks
            pattern = rf'\b{re.escape(en)}\b(?![^<]*>|[^>]*<\/)'
            if re.search(pattern, html):
                issues.append(f"建议：将 '{en}' 翻译为中文 '{zh}'")

        is_valid = not any(i.startswith("错误") for i in issues)
        return is_valid, issues

    def validate_content_completeness(self, html: str, analysis: Dict) -> Tuple[bool, List[str]]:
        """
        Validate that all key concepts from analysis are included.

        Args:
            html: HTML string to validate
            analysis: Content analysis dict with key_concepts

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        key_concepts = analysis.get('key_concepts', [])
        main_topics = analysis.get('main_topics', [])

        # Check for key concepts
        missing_concepts = []
        for concept in key_concepts:
            # Check if concept appears in HTML (outside of script/style tags)
            html_without_code = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL)
            if concept not in html_without_code:
                missing_concepts.append(concept)

        if missing_concepts:
            issues.append(f"警告：以下关键概念未在内容中找到：{', '.join(missing_concepts)}")

        # Check for main topics
        missing_topics = []
        for topic in main_topics:
            html_without_code = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL)
            if topic not in html_without_code:
                missing_topics.append(topic)

        if missing_topics:
            issues.append(f"建议：以下主题可能未充分覆盖：{', '.join(missing_topics)}")

        # Check for content hierarchy (H1, H2, H3)
        headings = {
            'h1': re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE),
            'h2': re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.IGNORECASE),
            'h3': re.findall(r'<h3[^>]*>(.*?)</h3>', html, re.IGNORECASE)
        }

        if not headings['h1']:
            issues.append("错误：缺少H1标题")
        if not headings['h2']:
            issues.append("建议：添加H2标题以组织内容结构")
        if not headings['h3'] and len(key_concepts) > 3:
            issues.append("建议：内容较多时，使用H3标题进一步细分")

        # Check for content length
        body_text = re.sub(r'<[^>]+>', '', html)
        body_text = re.sub(r'\s+', ' ', body_text).strip()

        if len(body_text) < 200:
            issues.append("警告：内容过少，可能不够完整")
        elif len(body_text) < 500:
            issues.append("建议：内容可以更详细一些")

        is_valid = not any(i.startswith("错误") for i in issues)
        return is_valid, issues

    def validate_reading_level(self, html: str, target_grade: int) -> Tuple[bool, List[str]]:
        """
        Validate that content matches target grade level.

        Args:
            html: HTML string to validate
            target_grade: Target grade level (0-14)

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Extract text content
        body_text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        body_text = re.sub(r'<style[^>]*>.*?</style>', '', body_text, flags=re.DOTALL)
        body_text = re.sub(r'<[^>]+>', '', body_text)
        body_text = re.sub(r'\s+', ' ', body_text).strip()

        if len(body_text) < 50:
            issues.append("警告：内容过少，无法评估阅读难度")
            return False, issues

        # Simple heuristics for reading level
        avg_sentence_length = len(body_text) / (body_text.count('。') + body_text.count('！') + body_text.count('？') + 1)

        # Check for complex vocabulary (longer words)
        long_words = len([w for w in body_text if len(w) > 4])
        complex_ratio = long_words / len(body_text.split()) if body_text.split() else 0

        # Grade level expectations
        if target_grade <= 6:  # Elementary
            if avg_sentence_length > 30:
                issues.append("建议：小学生内容句子过长，建议简化")
            if complex_ratio > 0.3:
                issues.append("建议：小学生内容应使用更简单的词汇")

        elif target_grade <= 9:  # Middle school
            if avg_sentence_length > 40:
                issues.append("建议：初中生内容句子可以适当简化")
        else:  # High school and above
            if avg_sentence_length < 15:
                issues.append("建议：高中生及以上内容可以增加句子复杂度")

        # Check for explanations
        if '即' not in body_text and '是指' not in body_text and '例如' not in body_text:
            issues.append("建议：添加解释和示例帮助理解")

        is_valid = not any(i.startswith("错误") for i in issues)
        return is_valid, issues

    def validate_interactive_elements(self, html: str) -> Tuple[bool, List[str]]:
        """
        Validate presence and quality of interactive elements.

        Args:
            html: HTML string to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Check for buttons
        buttons = re.findall(r'<button[^>]*>(.*?)</button>', html, re.IGNORECASE)
        if not buttons:
            issues.append("警告：缺少按钮元素")
        else:
            # Check for Chinese button text
            for btn_text in buttons:
                btn_text_clean = re.sub(r'<[^>]+>', '', btn_text).strip()
                if btn_text_clean and not self.chinese_pattern.search(btn_text_clean):
                    issues.append(f"建议：按钮文本应该是中文：'{btn_text_clean}'")

        # Check for quizzes or questions
        has_quiz = any(keyword in html.lower() for keyword in ['quiz', 'question', '问题', '题目', '测验'])
        if not has_quiz:
            issues.append("建议：添加测验或问题以检查学习效果")

        # Check for JavaScript functionality
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
        if not scripts:
            issues.append("建议：添加JavaScript实现交互功能")
        else:
            # Check for common interactive patterns
            script_content = ' '.join(scripts)
            interactive_patterns = ['addEventListener', 'onclick', 'function', 'querySelector']
            found_patterns = sum(1 for p in interactive_patterns if p in script_content)
            if found_patterns < 2:
                issues.append("建议：增强JavaScript交互功能")

        # Check for input elements
        has_input = any(tag in html for tag in ['<input', '<select', '<textarea'])
        if not has_input:
            issues.append("建议：考虑添加输入元素增强交互性")

        is_valid = not any(i.startswith("错误") for i in issues)
        return is_valid, issues

    def validate_all(self, html: str, analysis: Dict, user_preferences: Dict) -> Dict:
        """
        Run all content validations.

        Args:
            html: HTML string to validate
            analysis: Content analysis
            user_preferences: User preferences

        Returns:
            Dict with validation results
        """
        grade_level = user_preferences.get('grade_level', 6)

        validations = {
            'chinese': self.validate_chinese(html),
            'completeness': self.validate_content_completeness(html, analysis),
            'reading_level': self.validate_reading_level(html, grade_level),
            'interactive': self.validate_interactive_elements(html)
        }

        # Get overall summary
        all_issues = []
        all_valid = True
        validation_details = {}

        for name, (is_valid, issues) in validations.items():
            if not is_valid:
                all_valid = False
            all_issues.extend([f"[{name}] {issue}" for issue in issues])
            validation_details[name] = {
                'valid': is_valid,
                'issues': issues
            }

        return {
            'overall_valid': all_valid,
            'total_issues': len(all_issues),
            'issues': all_issues,
            'details': validation_details
        }
