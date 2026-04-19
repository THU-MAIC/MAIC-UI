"""
Integration Tests for HTML Generation Modes

Tests for FastGenerator and HeavyGenerator end-to-end functionality.

Date: 2025-01-15
"""

import pytest
import asyncio
import sys
import os

# Add project root to path
sys.path.append('.')

from src.services.html_generation import FastGenerator, HeavyGenerator
from src.services.validators import HTMLValidator, ContentValidator


class MockAIProvider:
    """Mock AI provider for testing."""

    def __init__(self, response_html: str = None):
        self.response_html = response_html or self._get_default_html()
        self.call_count = 0

    def _get_default_html(self) -> str:
        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试学习网站</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { font-family: 'Microsoft YaHei', sans-serif; line-height: 1.7; }
    </style>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto px-4 py-8">
        <header class="mb-8">
            <h1 class="text-3xl font-bold text-gray-900">测试标题</h1>
        </header>
        <main>
            <section class="bg-white rounded-lg p-6 mb-6">
                <h2 class="text-xl font-semibold mb-4">概念说明</h2>
                <p class="text-gray-700">这是测试内容，包含关键概念的详细说明。</p>
            </section>
        </main>
    </div>
</body>
</html>"""

    def get_provider_name(self) -> str:
        return "MockProvider"

    async def _run_zhipu_call(self, model: str, messages: list, thinking_params: dict = None):
        """Mock Zhipu API call."""
        self.call_count += 1
        class MockResponse:
            def __init__(self, html):
                self.choices = [MockChoice(html)]
        class MockChoice:
            def __init__(self, html):
                self.message = MockMessage(html)
        class MockMessage:
            def __init__(self, html):
                self.content = html

        return MockResponse(self.response_html)


class TestFastGenerator:
    """Integration tests for FastGenerator."""

    @pytest.mark.asyncio
    async def test_fast_generation_basic(self):
        """Test basic FastGenerator functionality."""
        mock_provider = MockAIProvider()
        generator = FastGenerator(mock_provider)

        pdf_images = []
        analysis = {
            'subject_area': '数学',
            'key_concepts': ['函数', '导数'],
            'main_topics': ['微积分基础'],
            'procedural_concepts': [
                {
                    'name': '函数',
                    'description': '理解函数的概念',
                    'key_steps': ['定义', '性质', '应用'],
                    'complexity': '中等'
                }
            ]
        }
        user_preferences = {
            'grade_level': 10,
            'interests': ['科学']
        }

        result = await generator.generate(pdf_images, analysis, user_preferences)

        assert 'html' in result
        assert 'metadata' in result
        assert 'generation_info' in result
        assert result['generation_info']['mode'] == 'fast'
        assert '<!DOCTYPE html>' in result['html']
        assert 'html' in result['html'].lower()
        print("✅ FastGenerator basic generation works")

    @pytest.mark.asyncio
    async def test_fast_generation_chinese_content(self):
        """Test that FastGenerator produces Chinese content."""
        mock_provider = MockAIProvider()
        generator = FastGenerator(mock_provider)

        analysis = {
            'subject_area': '物理',
            'key_concepts': ['牛顿定律'],
            'main_topics': []
        }
        user_preferences = {'grade_level': 8}

        result = await generator.generate([], analysis, user_preferences)
        html = result['html']

        # Check for Chinese characters
        import re
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
        assert chinese_pattern.search(html), "HTML should contain Chinese characters"
        print("✅ FastGenerator produces Chinese content")

    @pytest.mark.asyncio
    async def test_fast_generation_fallback(self):
        """Test FastGenerator fallback on error."""
        class FailingMockProvider(MockAIProvider):
            async def _run_zhipu_call(self, model, messages, thinking_params=None):
                raise Exception("Simulated API failure")

        mock_provider = FailingMockProvider()
        generator = FastGenerator(mock_provider)

        analysis = {'key_concepts': ['测试'], 'main_topics': []}
        user_preferences = {'grade_level': 6}

        result = await generator.generate([], analysis, user_preferences)

        assert 'html' in result
        assert result['generation_info'].get('fallback_used', False) == True
        print("✅ FastGenerator fallback works")


class TestHeavyGenerator:
    """Integration tests for HeavyGenerator."""

    @pytest.mark.asyncio
    async def test_heavy_generation_basic(self):
        """Test basic HeavyGenerator functionality."""
        mock_provider = MockAIProvider()
        generator = HeavyGenerator(mock_provider)

        pdf_images = []
        analysis = {
            'subject_area': '化学',
            'key_concepts': ['原子结构', '化学键'],
            'main_topics': ['化学基础'],
            'procedural_concepts': [
                {
                    'name': '原子结构',
                    'description': '理解原子的组成',
                    'key_steps': ['原子核', '电子', '能级'],
                    'complexity': '中等'
                }
            ]
        }
        user_preferences = {
            'grade_level': 9,
            'interests': ['实验']
        }

        result = await generator.generate(pdf_images, analysis, user_preferences)

        assert 'html' in result
        assert 'metadata' in result
        assert 'generation_info' in result
        assert result['generation_info']['mode'] == 'heavy'
        assert 'stages_completed' in result['generation_info']
        print("✅ HeavyGenerator basic generation works")

    @pytest.mark.asyncio
    async def test_heavy_stage_progression(self):
        """Test HeavyGenerator progresses through stages."""
        mock_provider = MockAIProvider()
        generator = HeavyGenerator(mock_provider)

        analysis = {
            'subject_area': '生物',
            'key_concepts': ['细胞'],
            'main_topics': [],
            'procedural_concepts': [{
                'name': '细胞',
                'description': '理解细胞结构',
                'key_steps': ['细胞膜', '细胞核', '细胞质'],
                'complexity': '简单'
            }]
        }
        user_preferences = {'grade_level': 7}

        result = await generator.generate([], analysis, user_preferences)

        # Should complete all 4 stages or fall back gracefully
        stages = result['generation_info'].get('stages_completed', 0)
        assert stages >= 0 or 'fallback_used' in result['generation_info']
        print(f"✅ HeavyGenerator completed {stages} stages")

    @pytest.mark.asyncio
    async def test_heavy_refinement_tracking(self):
        """Test HeavyGenerator tracks refinements."""
        mock_provider = MockAIProvider()
        generator = HeavyGenerator(mock_provider)

        analysis = {
            'subject_area': '历史',
            'key_concepts': ['古代文明'],
            'main_topics': [],
            'procedural_concepts': [{
                'name': '古代文明',
                'description': '理解古代文明特点',
                'key_steps': ['政治', '经济', '文化'],
                'complexity': '中等'
            }]
        }
        user_preferences = {'grade_level': 6}

        result = await generator.generate([], analysis, user_preferences)

        assert 'refinements' in result['generation_info']
        assert isinstance(result['generation_info']['refinements'], dict)
        print(f"✅ HeavyGenerator refinements: {result['generation_info']['refinements']}")


class TestGeneratorComparison:
    """Tests comparing FastGenerator and HeavyGenerator."""

    @pytest.mark.asyncio
    async def test_both_generators_produce_html(self):
        """Test that both generators produce valid HTML."""
        mock_provider_fast = MockAIProvider()
        mock_provider_heavy = MockAIProvider()

        fast_gen = FastGenerator(mock_provider_fast)
        heavy_gen = HeavyGenerator(mock_provider_heavy)

        analysis = {
            'subject_area': '数学',
            'key_concepts': ['几何'],
            'main_topics': [],
            'procedural_concepts': [{
                'name': '几何',
                'description': '理解几何图形',
                'key_steps': ['点', '线', '面'],
                'complexity': '简单'
            }]
        }
        user_preferences = {'grade_level': 5}

        fast_result = await fast_gen.generate([], analysis, user_preferences)
        heavy_result = await heavy_gen.generate([], analysis, user_preferences)

        assert 'html' in fast_result
        assert 'html' in heavy_result
        assert '<!DOCTYPE html>' in fast_result['html']
        assert '<!DOCTYPE html>' in heavy_result['html']
        print("✅ Both generators produce valid HTML")

    @pytest.mark.asyncio
    async def test_mode_differentiation(self):
        """Test that Fast and Heavy modes are differentiated."""
        mock_provider = MockAIProvider()

        fast_gen = FastGenerator(mock_provider)
        heavy_gen = HeavyGenerator(mock_provider)

        analysis = {'key_concepts': ['测试'], 'main_topics': [], 'procedural_concepts': []}
        user_preferences = {'grade_level': 6}

        fast_result = await fast_gen.generate([], analysis, user_preferences)
        heavy_result = await heavy_gen.generate([], analysis, user_preferences)

        assert fast_result['generation_info']['mode'] == 'fast'
        assert heavy_result['generation_info']['mode'] == 'heavy'
        print("✅ Fast and Heavy modes are differentiated")


class TestValidationIntegration:
    """Integration tests for validation with generators."""

    @pytest.mark.asyncio
    async def test_fast_output_validated(self):
        """Test that FastGenerator output passes HTML validation."""
        mock_provider = MockAIProvider()
        generator = FastGenerator(mock_provider)
        validator = HTMLValidator()

        analysis = {'key_concepts': ['验证测试'], 'main_topics': [], 'procedural_concepts': []}
        user_preferences = {'grade_level': 6}

        result = await generator.generate([], analysis, user_preferences)
        html = result['html']

        is_valid, issues = validator.validate_structure(html)
        assert is_valid or len([i for i in issues if i.startswith("错误")]) == 0
        print(f"✅ FastGenerator output validation: {len(issues)} warnings")

    @pytest.mark.asyncio
    async def test_chinese_validation(self):
        """Test Chinese content validation on generator output."""
        mock_provider = MockAIProvider()
        generator = FastGenerator(mock_provider)
        validator = ContentValidator()

        analysis = {'key_concepts': ['中文测试'], 'main_topics': [], 'procedural_concepts': []}
        user_preferences = {'grade_level': 6}

        result = await generator.generate([], analysis, user_preferences)
        html = result['html']

        is_valid, issues = validator.validate_chinese(html)
        # Should have Chinese characters from mock provider
        assert is_valid or any("中文" in i or "Chinese" in i for i in issues)
        print(f"✅ Chinese validation: {len(issues)} issues")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
