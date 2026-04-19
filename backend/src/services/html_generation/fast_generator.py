"""
Fast Generator Module

This module implements the Fast Mode generation, which uses one-shot prompting
for quick (~30 second) HTML generation. It maintains backward compatibility with
the existing ZhipuProvider implementation.


Date: 2025-01-15
"""

import json
import os
import time
import logging
from typing import Dict, List, Optional, Any

from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class FastGenerator(BaseGenerator):
    """
    Fast Mode HTML Generator.

    Uses one-shot AI prompting for quick HTML generation (~30 seconds).
    Maintains the existing behavior from ZhipuProvider.generate_website().
    """

    def __init__(self, ai_provider):
        """
        Initialize FastGenerator with an AI provider.

        Args:
            ai_provider: An instance of AIProvider (ZhipuProvider, EnglishProvider, etc.)
        """
        super().__init__(ai_provider)
        self.generation_metadata["mode"] = "FastGenerator"

    async def generate(self, pdf_images: List[Dict], analysis: Dict,
                     user_preferences: Dict) -> Dict[str, Any]:
        """
        Generate HTML using one-shot prompting (Fast Mode).

        Args:
            pdf_images: List of page images (not used in Fast Mode, only analysis)
            analysis: Content analysis with procedural_concepts
            user_preferences: User preferences for personalization

        Returns:
            Dict with html, metadata, and generation_info
        """
        generation_start = time.time()
        self.log_generation_start("Fast Mode")

        # Ensure language settings based on user preference
        user_preferences = self._ensure_language_settings(user_preferences)

        try:
            # Extract procedural concepts from analysis
            procedural_concepts = self._extract_procedural_concepts(analysis)

            # Generate HTML content using one-shot prompt
            html_content = await self._generate_html_content(
                procedural_concepts, analysis, user_preferences
            )

            # Generate metadata and interactive elements
            metadata_and_elements = await self._generate_metadata_and_interactive(
                procedural_concepts, analysis, user_preferences
            )

            generation_time = time.time() - generation_start

            # Combine results
            result = {
                "html": html_content,
                "metadata": {
                    **self._generate_metadata(analysis, user_preferences),
                    **metadata_and_elements.get("metadata", {})
                },
                "interactive_elements": metadata_and_elements.get("interactive_elements", []),
                "generation_info": {
                    "mode": "fast",
                    "duration_seconds": round(generation_time, 2),
                    "stages_completed": 1,
                    "refinements": {}
                }
            }

            self.log_generation_complete(generation_time)
            return result

        except Exception as e:
            self.log_error("fast_generation", e)
            generation_time = time.time() - generation_start
            logger.warning(f"⚠️ Fast generation failed, using fallback ({generation_time:.2f}s)")
            return self._generate_fallback(pdf_images, analysis, user_preferences)

    def _extract_procedural_concepts(self, analysis: Dict) -> List[Dict]:
        """
        Extract procedural concepts from analysis.

        Args:
            analysis: Content analysis

        Returns:
            List of procedural concepts
        """
        procedural_concepts = analysis.get('procedural_concepts', [])

        if not procedural_concepts:
            # Fallback: create procedural concepts from key_concepts
            procedural_concepts = [
                {
                    "name": concept,
                    "description": f"理解并应用{concept}的概念",
                    "key_steps": [
                        "步骤1：理解概念",
                        "步骤2：实践练习",
                        "步骤3：问题应用"
                    ],
                    "complexity": "中等"
                }
                for concept in analysis.get('key_concepts', [])[:2]
            ]

        # Limit to 2-3 concepts for Fast Mode
        return procedural_concepts[:3]

    async def _generate_html_content(self, procedural_concepts: List[Dict],
                                    analysis: Dict, user_preferences: Dict) -> str:
        """
        Generate HTML content using one-shot prompt.

        Args:
            procedural_concepts: List of procedural concepts to demonstrate
            analysis: Content analysis
            user_preferences: User preferences

        Returns:
            Generated HTML string
        """
        grade_level_int = user_preferences.get('grade_level', 6)
        grade_level = self._map_grade_level(grade_level_int)
        interests = user_preferences.get('interests', [])
        include_exercises = user_preferences.get('include_exercises', True)
        user_instruction = user_preferences.get('description', '无')

        logger.info(f"🎨 Generating HTML for {len(procedural_concepts)} concepts, grade {grade_level}")

        prompt = f"""请创建一个交互式学习网站来演示程序性知识，参考以下示例：

        示例网站结构（来自 Compiler Explorer: Lexical Analysis）：
        - 分为左右两栏布局
        - 左侧：输入区域，用户可以进行实践操作
        - 右侧：输出区域，实时显示处理结果
        - 包含清晰的步骤说明和视觉反馈

        现在请为以下程序性概念创建类似的学习网站：

        程序性概念：
        {json.dumps(procedural_concepts, ensure_ascii=False, indent=2)}

        用户画像：
        - 年级: {grade_level}
        - 兴趣: {', '.join(interests) if interests else '综合学习'}

        用户的特殊需求:
        {user_instruction}

        要求：
        1. 创建完整的HTML文档，包含<!DOCTYPE html>到</html>
        2. 使用现代化CSS样式（类似示例的深色主题）
        3. 实现交互功能：用户输入 -> 处理 -> 输出反馈
        4. 为每个程序性概念创建可视化演示
        5. 包含步骤指导和学习提示
        6. 适合{grade_level}年级学生理解和使用
        7. **所有用户可见内容必须使用简体中文**
        8. **禁止使用Markdown代码块，不要输出```html或```**

        请只返回纯净的HTML代码，不要包含其他解释。"""

        response = await self._call_ai_provider(prompt, thinking_enabled=True)

        if response:
            return self._extract_html_from_response(response)

        return self._generate_fallback_html([], analysis, user_preferences)

    async def _generate_metadata_and_interactive(self, procedural_concepts: List[Dict],
                                                analysis: Dict, user_preferences: Dict) -> Dict:
        """
        Generate metadata and interactive elements.

        Args:
            procedural_concepts: List of procedural concepts
            analysis: Content analysis
            user_preferences: User preferences

        Returns:
            Dict with metadata and interactive_elements
        """
        include_exercises = user_preferences.get('include_exercises', True)
        grade_level_int = user_preferences.get('grade_level', 6)
        grade_level = self._map_grade_level(grade_level_int)
        interests = user_preferences.get('interests', [])
        if include_exercises:
            prompt = f"""请为程序性知识学习网站生成元数据和交互式测验元素。

        程序性概念：
        {json.dumps(procedural_concepts, ensure_ascii=False, indent=2)}

        用户画像：
        - 年级: {grade_level}
        - 兴趣: {', '.join(interests) if interests else '综合学习'}

        内容分析：
        - 学科: {analysis.get('subject_area', '综合教育')}
        - 主题: {', '.join(analysis.get('main_topics', []))}
        - 关键概念: {', '.join(analysis.get('key_concepts', []))}

        请生成以下内容：

        1. 元数据(metadata):
        - title: 适合{grade_level}年级的程序性知识学习标题
        - subject: 学科名称
        - grade_level: 年级水平
        - estimated_time_minutes: 预计学习时间(20-40分钟)
        - learning_objectives: 2-4个程序性学习目标

        2. 交互元素(interactive_elements):
        - 生成3-5个测验题目，专门检查学生对程序性知识的理解：
            * quiz: 针对程序步骤的选择题
            * quiz: 识别正确顺序的排序题
            * quiz: 应用场景分析题
            * vocabulary: 程序性相关术语定义

        **所有文本内容必须使用简体中文。**

        请只回复JSON格式:
        {{
            "metadata": {{
                "title": "网站标题",
                "subject": "学科",
                "grade_level": "{grade_level}",
                "estimated_time_minutes": 30,
                "learning_objectives": ["目标1", "目标2", "目标3"]
            }},
            "interactive_elements": [
                {{
                    "type": "quiz",
                    "question": "关于程序性问题",
                    "options": ["选项A", "选项B", "选项C", "选项D"],
                    "correct_answer": 0,
                    "explanation": "答案解释"
                }},
                {{
                    "type": "vocabulary",
                    "word": "程序性术语",
                    "definition": "术语定义"
                }}
            ]
        }}"""

        else:
            prompt = f"""请为程序性知识学习网站生成元数据和交互式测验元素。

        程序性概念：
        {json.dumps(procedural_concepts, ensure_ascii=False, indent=2)}

        用户画像：
        - 年级: {grade_level}
        - 兴趣: {', '.join(interests) if interests else '综合学习'}

        内容分析：
        - 学科: {analysis.get('subject_area', '综合教育')}
        - 主题: {', '.join(analysis.get('main_topics', []))}
        - 关键概念: {', '.join(analysis.get('key_concepts', []))}

        请生成以下内容：

        1. 元数据(metadata):
        - title: 适合{grade_level}年级的程序性知识学习标题
        - subject: 学科名称
        - grade_level: 年级水平
        - estimated_time_minutes: 预计学习时间(20-40分钟)
        - learning_objectives: 2-4个程序性学习目标

        **所有文本内容必须使用简体中文。**

        请只回复JSON格式:
        {{
            "metadata": {{
                "title": "网站标题",
                "subject": "学科",
                "grade_level": "{grade_level}",
                "estimated_time_minutes": 30,
                "learning_objectives": ["目标1", "目标2", "目标3"]
            }},
            "interactive_elements": []
        }}"""

        response = await self._call_ai_provider(prompt, thinking_enabled=False)

        if response:
            return self._extract_json_from_response(response)

        return self._generate_fallback_metadata(analysis, user_preferences)

    async def _call_ai_provider(self, prompt: str, thinking_enabled: bool = True) -> Optional[str]:
        """
        Call the AI provider with a prompt.

        Args:
            prompt: Prompt to send
            thinking_enabled: Whether to enable thinking mode

        Returns:
            Response content or None
        """
        try:
            backend = getattr(self.provider, 'backend', None)

            async def _call_zhipu() -> Optional[str]:
                response = await self.provider._run_zhipu_call(
                    model=getattr(self.provider, 'text_model', os.getenv('ZHIPU_TEXT_MODEL', 'glm-4.6')),
                    messages=[{"role": "user", "content": prompt}],
                    thinking_params={"type": "enabled" if thinking_enabled else "disabled"},
                )
                if response and response.choices and response.choices[0].message:
                    return response.choices[0].message.content
                return None

            async def _call_anthropic() -> Optional[str]:
                response = await self.provider._run_anthropic_call(
                    model=getattr(self.provider, 'model', 'claude-sonnet-4-6'),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=64000,  # Increased for long HTML generation
                    thinking_enabled=thinking_enabled
                )
                # Anthropic returns content as a list of content blocks
                if response and response.content:
                    content_text = ""
                    for block in response.content:
                        if hasattr(block, 'text'):
                            content_text += block.text
                    return content_text
                return None

            # Prefer explicit backend routing for providers that implement multiple methods.
            if backend == 'anthropic' and hasattr(self.provider, '_run_anthropic_call'):
                result = await _call_anthropic()
                if result is not None:
                    return result

            elif backend == 'zhipu' and hasattr(self.provider, '_run_zhipu_call'):
                result = await _call_zhipu()
                if result is not None:
                    return result

            # Fallback routing: use whichever client is actually initialized.
            elif hasattr(self.provider, '_run_anthropic_call') and getattr(self.provider, 'anthropic_client', None) is not None:
                result = await _call_anthropic()
                if result is not None:
                    return result

            elif hasattr(self.provider, '_run_zhipu_call') and getattr(self.provider, 'zhipu_client', None) is not None:
                result = await _call_zhipu()
                if result is not None:
                    return result

            elif hasattr(self.provider, 'client'):
                # Generic provider with OpenAI-style client
                import asyncio
                def _sync_call():
                    return self.provider.client.chat.completions.create(
                        model=getattr(self.provider, 'model', 'gpt-4'),
                        messages=[{"role": "user", "content": prompt}]
                    )
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, _sync_call)
                if response and response.choices and response.choices[0].message:
                    return response.choices[0].message.content

            else:
                logger.error("❌ Unknown AI provider type")
                return None

        except Exception as e:
            logger.error(f"❌ AI provider call failed: {e}")

        return None

    def _extract_html_from_response(self, response: str) -> str:
        """
        Extract HTML from AI response.

        Args:
            response: Response string from AI

        Returns:
            Extracted HTML
        """
        cleaned = self._sanitize_html_output(response)

        html_start = cleaned.find('<!DOCTYPE html>')
        if html_start == -1:
            html_start = cleaned.find('<html')

        html_end_index = cleaned.rfind('</html>')
        html_end = html_end_index + len('</html>') if html_end_index != -1 else -1

        if html_start != -1 and html_end > html_start:
            return cleaned[html_start:html_end]

        if html_start != -1:
            return cleaned[html_start:]

        # If no HTML tags found, return full response
        return cleaned

    def _extract_json_from_response(self, response: str) -> Dict:
        """
        Extract JSON from AI response.

        Args:
            response: Response string from AI

        Returns:
            Parsed JSON dict or fallback
        """
        json_start = response.find('{')
        json_end = response.rfind('}') + 1

        if json_start != -1 and json_end > json_start:
            try:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # Return fallback
        return {"metadata": {}, "interactive_elements": []}

    def _map_grade_level(self, grade_level: int) -> str:
        """
        Convert integer grade level to Chinese string.

        Args:
            grade_level: Integer grade (0-14)

        Returns:
            Chinese grade level string
        """
        grade_mapping = {
            0: "幼儿园", 1: "小学一年级", 2: "小学二年级",
            3: "小学三年级", 4: "小学四年级", 5: "小学五年级",
            6: "小学六年级", 7: "初中一年级", 8: "初中二年级",
            9: "初中三年级", 10: "高中一年级", 11: "高中二年级",
            12: "高中三年级", 13: "本科", 14: "研究生"
        }
        return grade_mapping.get(grade_level, f"年级{grade_level}")

    def _generate_fallback_html(self, pdf_images: List[Dict], analysis: Dict,
                                user_preferences: Dict) -> str:
        """Generate fallback HTML when generation fails."""
        user_preferences = user_preferences or {}
        grade_level_int = user_preferences.get('grade_level', 6)
        grade_level = self._map_grade_level(grade_level_int)
        subject = analysis.get('subject_area', '教育')
        topics = analysis.get('main_topics', ['学习'])

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>交互式学习 - {subject}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-green-50 to-blue-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <header class="mb-8 text-center">
            <h1 class="text-4xl font-bold text-green-600 mb-2">交互式学习平台</h1>
            <p class="text-gray-600">学科: {subject} | 年级: {grade_level} | 快速生成模式</p>
        </header>

        <nav class="mb-8">
            <div class="flex flex-wrap gap-2 justify-center">
                <button class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">概览</button>
                <button class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">内容学习</button>
                <button class="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600">练习测试</button>
            </div>
        </nav>

        <main class="space-y-8">
            <section class="bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-semibold mb-4">学习主题</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {"".join([f'<div class="bg-green-50 p-4 rounded-lg"><h3 class="font-semibold">{topic}</h3><p class="text-sm text-gray-600">重要学习内容</p></div>' for topic in topics])}
                </div>
            </section>

            <section class="bg-blue-50 rounded-lg p-6">
                <h3 class="text-xl font-semibold mb-3">学习进度</h3>
                <div class="w-full bg-gray-200 rounded-full h-4">
                    <div id="progress-bar" class="bg-blue-600 h-4 rounded-full transition-all duration-300" style="width: 0%"></div>
                </div>
                <p class="text-center mt-2 text-gray-600">完成进度: <span id="progress-text">0%</span></p>
            </section>

            <section class="bg-purple-50 rounded-lg p-6">
                <h3 class="text-xl font-semibold mb-3">学习活动</h3>
                <div class="space-y-4">
                    <button onclick="updateProgress(25)" class="w-full bg-purple-500 text-white py-2 px-4 rounded hover:bg-purple-600">开始学习内容</button>
                    <button onclick="updateProgress(50)" class="w-full bg-indigo-500 text-white py-2 px-4 rounded hover:bg-indigo-600">完成练习</button>
                    <button onclick="updateProgress(100)" class="w-full bg-green-500 text-white py-2 px-4 rounded hover:bg-green-600">完成评估</button>
                </div>
            </section>
        </main>
    </div>

    <script>
        let currentProgress = 0;
        function updateProgress(progress) {{
            currentProgress = Math.max(currentProgress, progress);
            document.getElementById('progress-bar').style.width = currentProgress + '%';
            document.getElementById('progress-text').textContent = currentProgress + '%';
        }}
    </script>
</body>
</html>"""

    def _generate_fallback_metadata(self, analysis: Dict, user_preferences: Dict) -> Dict:
        """Generate fallback metadata when generation fails."""
        user_preferences = user_preferences or {}
        grade_level_int = user_preferences.get('grade_level', 6)
        grade_level = self._map_grade_level(grade_level_int)
        subject = analysis.get('subject_area', '教育')
        concepts = analysis.get('key_concepts', ['概念', '理解'])

        return {
            "metadata": {
                "title": f"交互式{subject}学习",
                "subject": subject,
                "grade_level": grade_level,
                "estimated_time_minutes": 30,
                "learning_objectives": [
                    f"理解{subject}的基本概念",
                    "掌握相关学习方法",
                    "完成学习评估"
                ]
            },
            "interactive_elements": [
                {
                    "type": "quiz",
                    "question": f"关于{subject}，以下哪个描述是正确的？",
                    "options": ["选项A：基本概念", "选项B：应用方法", "选项C：高级技巧", "选项D：综合实践"],
                    "correct_answer": 0,
                    "explanation": f"这是{subject}学习的基础概念"
                },
                {
                    "type": "vocabulary",
                    "word": concepts[0] if concepts else "重要概念",
                    "definition": f"{subject}领域的核心概念，需要重点理解和掌握"
                }
            ]
        }

    def _generate_fallback(self, pdf_images: List[Dict], analysis: Dict,
                          user_preferences: Dict) -> Dict:
        """Generate complete fallback response."""
        return {
            "html": self._generate_fallback_html(pdf_images, analysis, user_preferences),
            "metadata": self._generate_fallback_metadata(analysis, user_preferences)["metadata"],
            "interactive_elements": self._generate_fallback_metadata(analysis, user_preferences)["interactive_elements"],
            "generation_info": {
                "mode": "fast",
                "fallback_used": True,
                "stages_completed": 0,
                "refinements": {}
            }
        }
