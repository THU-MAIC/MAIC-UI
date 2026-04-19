"""
Template Customizer Service

Uses LLM intelligence to customize template HTML based on user content and preferences.
Instead of simple placeholder replacement, the LLM:
- Understands the template structure and preserves it
- Intelligently adapts content based on user input
- Maintains consistency with the template's design philosophy
"""

import json
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TemplateCustomizer:
    """
    Customize template HTML using LLM intelligence.

    The LLM receives:
    1. Base template HTML
    2. Content information (title, description, concepts)
    3. User preferences (grade level, interests)
    4. Customization hints from template

    The LLM returns:
    - Customized HTML with preserved core structure
    - Modified content to match user's needs
    - Adjusted parameters and examples
    """

    def __init__(self, ai_provider):
        """
        Initialize template customizer with an AI provider.

        Args:
            ai_provider: An instance of AIProvider (ZhipuProvider, EnglishProvider, etc.)
        """
        self.ai_provider = ai_provider

    async def customize_template(
        self,
        template,
        content_info: Dict,
        user_preferences: Dict,
        customization_params: Optional[Dict] = None
    ) -> str:
        """
        Customize template HTML using LLM.

        Args:
            template: DemoTemplate instance
            content_info: Dict with content information
            user_preferences: Dict with user preferences
            customization_params: Optional additional customization parameters

        Returns:
            Customized HTML string
        """
        try:
            # Load base template HTML
            base_html = template.get_html_template()

            # Build workflow-specific customization prompt
            prompt = self._build_customization_prompt(
                workflow_type=template.workflow_type,
                template=template,
                base_html=base_html,
                content_info=content_info,
                user_preferences=user_preferences,
                customization_params=customization_params
            )

            # Call LLM for customization
            customized_html = await self._call_llm_for_customization(
                prompt
            )

            # Validate that structure is preserved
            if self._validate_customized_html(customized_html, base_html):
                return customized_html
            else:
                logger.warning("LLM customization failed validation, using fallback")
                return self._generate_fallback_html(template, content_info)

        except Exception as e:
            logger.error(f"Error customizing template: {e}")
            return self._generate_fallback_html(template, content_info)

    def _build_customization_prompt(
        self,
        workflow_type: str,
        template,
        base_html: str,
        content_info: Dict,
        user_preferences: Dict,
        customization_params: Optional[Dict] = None
    ) -> str:
        """Build workflow-specific customization prompt."""

        if workflow_type == 'ppt_demo':
            return self._build_ppt_prompt(
                template, base_html, content_info, user_preferences, customization_params
            )
        elif workflow_type == 'website_pdf':
            return self._build_website_pdf_prompt(
                template, base_html, content_info, user_preferences, customization_params
            )
        elif workflow_type == 'website_concept':
            return self._build_website_concept_prompt(
                template, base_html, content_info, user_preferences, customization_params
            )
        else:
            return self._build_generic_prompt(
                template, base_html, content_info, user_preferences
            )

    def _build_ppt_prompt(
        self,
        template,
        base_html: str,
        content_info: Dict,
        user_preferences: Dict,
        customization_params: Optional[Dict] = None
    ) -> str:
        """Build PPT demo customization prompt."""

        title = content_info.get('title', '演示')
        description = content_info.get('description', '')
        demo_type = content_info.get('demo_type', 'simulation')
        grade_level = user_preferences.get('grade_level', 8)
        interests = user_preferences.get('interests', [])

        # Map grade level to Chinese
        grade_map = {
            6: '初一', 7: '初二', 8: '初三', 9: '高一',
            10: '高二', 11: '高三', 12: '大学预备'
        }
        grade_cn = grade_map.get(grade_level, f'{grade_level}年级')

        return f"""你是交互式演示定制专家。请定制这个PPT演示模板。

【模板】{template.display_name}
【用途】{demo_type}演示

【原始模板HTML】
{base_html[:50000]}

【定制内容】
- 标题: {title}
- 描述: {description}
- 演示类型: {demo_type}
- 演示原因: 需要逐步可视化过程

【学生】{grade_cn}，兴趣: {', '.join(interests) if interests else '综合学习'}

【定制要求】
1. 保持模板的核心交互逻辑和视觉设计
2. 修改标题、描述等文本内容以匹配定制内容
3. 根据演示类型调整功能说明和示例
4. 确保适合{grade_cn}学生理解
5. 保持所有JavaScript和CSS功能完整
6. 不要破坏模板的响应式布局

【额外参数】
{json.dumps(customization_params, ensure_ascii=False) if customization_params else '无'}

请只返回定制的HTML代码，不要包含其他解释。"""

    def _build_website_pdf_prompt(
        self,
        template,
        base_html: str,
        content_info: Dict,
        user_preferences: Dict,
        customization_params: Optional[Dict] = None
    ) -> str:
        """Build website from PDF customization prompt."""

        subject = content_info.get('subject', '科学')
        topics = content_info.get('topics', [])
        concepts = content_info.get('concepts', [])
        grade_level = user_preferences.get('grade_level', 8)

        # Map grade level to Chinese
        grade_map = {
            6: '初一', 7: '初二', 8: '初三', 9: '高一',
            10: '高二', 11: '高三', 12: '大学预备'
        }
        grade_cn = grade_map.get(grade_level, f'{grade_level}年级')

        return f"""你是交互式学习网站专家。请根据PDF分析定制这个网站模板。

【模板】{template.display_name}
【学科】{subject}

【原始模板HTML】
{base_html[:50000]}

【PDF分析】
- 学科: {subject}
- 主题: {', '.join(topics) if topics else '综合主题'}
- 概念: {', '.join(concepts[:5]) if concepts else '核心概念'}

【学生】{grade_cn}

【定制要求】
1. 保持模板的导航和布局结构
2. 整合PDF的关键主题和概念
3. 根据内容调整实验和模拟部分
4. 保持所有交互功能可工作
5. 确保适合{grade_cn}学生理解
6. 添加与主题相关的实际例子

请只返回定制的HTML代码，不要包含其他解释。"""

    def _build_website_concept_prompt(
        self,
        template,
        base_html: str,
        content_info: Dict,
        user_preferences: Dict,
        customization_params: Optional[Dict] = None
    ) -> str:
        """Build website from concept customization prompt."""

        concept_name = content_info.get('concept_name', '知识点')
        concept_overview = content_info.get('concept_overview', '')
        mastery_points = content_info.get('mastery_points', '')
        design_idea = content_info.get('design_idea', '')
        grade_level = user_preferences.get('grade_level', 9)

        # Map grade level to Chinese
        grade_map = {
            6: '初一', 7: '初二', 8: '初三', 9: '高一',
            10: '高二', 11: '高三', 12: '大学预备'
        }
        grade_cn = grade_map.get(grade_level, f'{grade_level}年级')

        return f"""你是交互式教学专家。请根据知识点定制这个学习网站模板。

【模板】{template.display_name}
【知识点】{concept_name}

【原始模板HTML】
{base_html[:50000]}

【知识点详情】
- 概述: {concept_overview}
- 掌握要点: {mastery_points}
- 设计思路: {design_idea}

【学生】{grade_cn}

【定制要求】
1. 根据设计思路实现交互组件
2. 为每个掌握要点创建学习模块
3. 提供清晰指导和即时反馈
4. 保持模板的视觉风格
5. 确保适合{grade_cn}学生理解
6. 添加知识点相关的例子和练习

请只返回定制的HTML代码，不要包含其他解释。"""

    def _build_generic_prompt(
        self,
        template,
        base_html: str,
        content_info: Dict,
        user_preferences: Dict
    ) -> str:
        """Build generic customization prompt."""
        return f"""请根据以下内容定制HTML模板。

【模板】{template.display_name}

【原始模板HTML】
{base_html[:50000]}

【内容信息】
{json.dumps(content_info, ensure_ascii=False, indent=2)}

【用户偏好】
{json.dumps(user_preferences, ensure_ascii=False, indent=2)}

请保持模板的核心结构和功能，根据内容信息调整文本和示例。
只返回定制的HTML代码，不要包含其他解释。"""

    async def _call_llm_for_customization(self, prompt: str) -> str:
        """Call LLM for template customization."""

        # Use the AI provider's text generation capability
        # For ZhipuProvider, we can use the existing methods

        try:
            # Check if provider has a method for text-only generation
            if hasattr(self.ai_provider, '_run_zhipu_call'):
                # ZhipuProvider
                response = await self.ai_provider._run_zhipu_call(
                    model=self.ai_provider.text_model,
                    messages=[{"role": "user", "content": prompt}],
                    thinking_params={"type": "enabled"},
                    max_tokens=64000  # Increased for long HTML generation
                )

                if response and response.choices and response.choices[0].message:
                    content_text = response.choices[0].message.content

                    # Extract HTML from response
                    html_start = content_text.find('<!DOCTYPE html>')
                    if html_start == -1:
                        html_start = content_text.find('<html')

                    html_end_index = content_text.rfind('</html>')
                    html_end = html_end_index + len('</html>') if html_end_index != -1 else -1

                    if html_start != -1 and html_end > html_start:
                        return content_text[html_start:html_end]
                    elif html_start != -1:
                        # No closing tag found, return from start to end
                        return content_text[html_start:]
                    else:
                        return content_text

            # Fallback for other providers
            logger.warning("LLM provider doesn't support customization, returning prompt as-is")
            return prompt

        except Exception as e:
            logger.error(f"Error calling LLM for customization: {e}")
            raise

    def _validate_customized_html(self, customized_html: str, base_html: str) -> bool:
        """Validate that customized HTML preserves core structure."""
        # Basic validation checks
        if not customized_html:
            return False

        # Check for essential HTML tags
        if '<!DOCTYPE html>' not in customized_html and '<html' not in customized_html:
            return False

        if '</html>' not in customized_html:
            return False

        return True

    def _generate_fallback_html(self, template, content_info: Dict) -> str:
        """Generate fallback HTML when customization fails."""
        try:
            # Try to return the original template HTML
            return template.get_html_template()
        except:
            # If that fails, return a basic error HTML
            return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{template.display_name}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-2xl font-bold">{template.display_name}</h1>
        <p>模板定制暂时不可用，显示原始内容。</p>
        <p>内容: {content_info.get('title', 'N/A')}</p>
    </div>
</body>
</html>"""
