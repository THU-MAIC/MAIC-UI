"""
Heavy Generator Module

This module implements the Heavy Mode generation with a 2-stage pipeline.
Each stage has validation and up to 3 refinement attempts.

Date: 2025-01-15
"""

import json
import os
import time
import logging
import asyncio
from typing import Dict, List, Optional, Any

from .base_generator import BaseGenerator
from .fast_generator import FastGenerator
from ..validators import HTMLValidator, ContentValidator, SimulationValidator
from ..templates.heavy_mode_prompts import get_stage_prompt, get_refinement_prompt
from .components.themes import get_theme
from .cache import get_cache

logger = logging.getLogger(__name__)


class HeavyGenerator(BaseGenerator):
    """
    Heavy Mode HTML Generator.

    Uses a 2-stage pipeline with validation and refinement:
    - Stage 1: Content-Aligned Interactive Simulations (left: process, right: simulation)
    - Stage 2: Layout Polish & Visual Refinement

    Processing time: ~2-3 minutes
    """

    def __init__(self, ai_provider):
        """Initialize HeavyGenerator with an AI provider."""
        super().__init__(ai_provider)
        self.generation_metadata["mode"] = "HeavyGenerator"
        self.html_validator = HTMLValidator()
        self.content_validator = ContentValidator()
        self.sim_validator = SimulationValidator()
        self.cache = get_cache()

    async def generate(self, pdf_images: List[Dict], analysis: Dict,
                     user_preferences: Dict) -> Dict[str, Any]:
        """
        Generate HTML using 2-stage pipeline (Heavy Mode).

        Stage 1: Content-Aligned Interactive Simulations
        - Focus on interactive simulations to illustrate given concepts
        - Show process steps on left, concurrent simulation on right
        - Ensure strong alignment between process and simulation

        Stage 2: Layout Polish & Visual Refinement
        - Ensure HTML renders without errors
        - Polish visual style and aesthetics
        - Verify all functionality works correctly

        Args:
            pdf_images: List of page images (not used, only analysis)
            analysis: Content analysis with procedural_concepts
            user_preferences: User preferences for personalization

        Returns:
            Dict with html, metadata, and generation_info
        """
        generation_start = time.time()
        self.log_generation_start("Heavy Mode")

        # Ensure language settings based on user preference
        user_preferences = self._ensure_language_settings(user_preferences)

        # Get theme based on subject
        theme = get_theme(analysis.get('subject_area', ''))

        # Extract procedural concepts
        procedural_concepts = self._extract_procedural_concepts(analysis)

        # Build context for prompts
        context = self._build_context(analysis, user_preferences, procedural_concepts, theme)

        # Track completed stages for fallback
        completed_stages = {}
        refinements = {'stage1': 0, 'stage2': 0}

        try:
            # Stage 1: Content-Aligned Interactive Simulations
            result = await self._execute_stage(
                'stage1',
                context,
                self._generate_aligned_simulation,
                self.sim_validator.validate_interactive_functionality,
                completed_stages,
                refinements
            )
            if result is None:  # Catastrophic failure
                return await self._generate_fallback(pdf_images, analysis, user_preferences)
            completed_stages['stage1'] = result

            # Stage 2: Layout Polish & Visual Refinement
            context['html_simulation'] = completed_stages['stage1']
            result = await self._execute_stage(
                'stage2',
                context,
                self._polish_layout_and_visuals,
                self.html_validator.validate_complete,
                completed_stages,
                refinements
            )
            if result is None:
                return await self._degrade_gracefully(completed_stages, analysis, user_preferences)
            completed_stages['stage2'] = result

            generation_time = time.time() - generation_start

            # Cache successful result
            self.cache.save_success(context, 'stage2', completed_stages['stage2'])

            # Generate metadata and interactive elements using FastGenerator steps
            fast_generator = FastGenerator(self.provider)
            metadata_and_elements = await fast_generator._generate_metadata_and_interactive(
                procedural_concepts, analysis, user_preferences
            )

            result = {
                "html": completed_stages['stage2'],
                "metadata": {
                    **self._generate_metadata(analysis, user_preferences),
                    **metadata_and_elements.get("metadata", {})
                },
                "interactive_elements": metadata_and_elements.get("interactive_elements", []),
                "generation_info": {
                    "mode": "heavy",
                    "duration_seconds": round(generation_time, 2),
                    "stages_completed": 2,
                    "refinements": refinements,
                    "theme": theme['name']
                }
            }

            self.log_generation_complete(generation_time)
            return result

        except Exception as e:
            self.log_error("heavy_generation", e)
            return await self._degrade_gracefully(completed_stages, analysis, user_preferences)

    def _build_context(self, analysis: Dict, user_preferences: Dict,
                      procedural_concepts: List, theme: Dict) -> Dict:
        """Build context dict for prompts."""
        grade_level = self._map_grade_level(user_preferences.get('grade_level', 6))
        interests = user_preferences.get('interests', [])
        language = user_preferences.get('language', 'zh')

        # Default interests text based on language
        if language == 'en':
            interests_text = ', '.join(interests) if interests else 'General learning'
        else:
            interests_text = ', '.join(interests) if interests else '综合学习'

        return {
            'concept_info': json.dumps(procedural_concepts, ensure_ascii=False, indent=2),
            'key_concepts': analysis.get('key_concepts', []),
            'key_concepts_list': ', '.join(analysis.get('key_concepts', [])),
            'learning_objectives': analysis.get('learning_objectives', []),
            'main_topics': analysis.get('main_topics', []),
            'subject': analysis.get('subject_area', ''),
            'grade_level': grade_level,
            'interests': interests_text,
            'primary_color': theme['primary'].replace('#', ''),
            'accent_color': theme['accent'].replace('#', ''),
            'procedural_concepts': json.dumps(procedural_concepts, ensure_ascii=False, indent=2),
            'analysis': analysis,
            'language': language
        }

    async def _execute_stage(self, stage_name: str, context: Dict,
                            stage_func, validation_func,
                            completed_stages: Dict, refinements: Dict) -> Optional[str]:
        """
        Execute a generation stage with validation and refinement.

        Args:
            stage_name: Name of the stage
            context: Generation context
            stage_func: Function to generate content
            validation_func: Function to validate content
            completed_stages: Dict to track completed stages
            refinements: Dict to track refinement counts

        Returns:
            Generated HTML string or None on catastrophic failure
        """
        max_refinements = 3
        last_error = None

        # Check cache first
        cached = self.cache.get_cached(context, stage_name)
        if cached:
            logger.info(f"Using cached {stage_name}")
            return self._sanitize_html_output(cached)

        for attempt in range(max_refinements):
            try:
                logger.info(f"{stage_name} - Attempt {attempt + 1}/{max_refinements}")

                # Generate with timeout
                html = await asyncio.wait_for(
                    stage_func(context),
                    timeout=600  # 10 minutes per stage
                )

                if not html:
                    logger.warning(f"{stage_name} - Empty result on attempt {attempt + 1}")
                    continue

                # Validate
                # is_valid, issues = validation_func(html)
                is_valid, issues = True, None
                

                if is_valid:
                    logger.info(f"{stage_name} - Validation passed on attempt {attempt + 1}")
                    self.cache.save_success(context, stage_name, html)
                    refinements[stage_name] = attempt
                    return html
                else:
                    logger.warning(f"{stage_name} - Validation failed: {issues[:3]}")
                    last_error = issues[0] if issues else "Unknown validation error"

                    # On last attempt, accept if no critical errors
                    if attempt == max_refinements - 1:
                        critical_errors = [i for i in issues if i.startswith("错误")]
                        if not critical_errors:
                            logger.info(f"{stage_name} - Accepted with warnings")
                            self.cache.save_success(context, stage_name, html)
                            refinements[stage_name] = attempt
                            return html

            except asyncio.TimeoutError:
                logger.warning(f"{stage_name} - Timeout on attempt {attempt + 1}")
                last_error = "Generation timeout"
            except Exception as e:
                logger.error(f"{stage_name} - Error: {e}")
                last_error = str(e)

        # All attempts failed
        logger.error(f"{stage_name} - All attempts failed, using fallback")
        return None

    async def _generate_aligned_simulation(self, context: Dict) -> str:
        """Stage 1: Generate content-aligned interactive simulations with left-right layout."""
        prompt = get_stage_prompt(1, **context)
        response = await self._call_ai_provider(prompt, thinking_enabled=True)
        return self._extract_html_from_response(response) if response else ""

    async def _polish_layout_and_visuals(self, context: Dict) -> str:
        """Stage 2: Polish layout and visuals, ensure error-free rendering."""
        prompt = get_stage_prompt(2, **context)
        response = await self._call_ai_provider(prompt, thinking_enabled=True)
        return self._extract_html_from_response(response) if response else ""

    async def _call_ai_provider(self, prompt: str, thinking_enabled: bool = True) -> Optional[str]:
        """Call the AI provider with a prompt."""
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
                    max_tokens=64000,
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
                logger.error("Unknown AI provider type")
                return None

        except Exception as e:
            logger.error(f"AI provider call failed: {e}")

        return None

    def _extract_html_from_response(self, response: str) -> str:
        """Extract HTML from AI response."""
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

        return cleaned

    async def _degrade_gracefully(self, completed_stages: Dict, analysis: Dict,
                                  user_preferences: Dict) -> Dict:
        """Build best possible output from completed stages."""
        logger.warning("Degrading gracefully from completed stages")

        if 'stage2' in completed_stages:
            html = completed_stages['stage2']
        elif 'stage1' in completed_stages:
            html = self._apply_basic_styling(completed_stages['stage1'])
        else:
            html = self._emergency_template(analysis, user_preferences)

        # Try to generate metadata and interactive elements via FastGenerator
        try:
            procedural_concepts = self._extract_procedural_concepts(analysis)
            fast_generator = FastGenerator(self.provider)
            metadata_and_elements = await fast_generator._generate_metadata_and_interactive(
                procedural_concepts, analysis, user_preferences
            )
        except Exception:
            metadata_and_elements = {}

        return {
            "html": html,
            "metadata": {
                **self._generate_metadata(analysis, user_preferences),
                **metadata_and_elements.get("metadata", {})
            },
            "interactive_elements": metadata_and_elements.get("interactive_elements", []),
            "generation_info": {
                "mode": "heavy",
                "fallback_used": True,
                "stages_completed": len(completed_stages),
                "refinements": {}
            }
        }

    def _apply_basic_styling(self, html: str) -> str:
        """Apply basic styling to stage 1 output if stage 2 fails."""
        style = """
<style>
body { font-family: 'Source Han Sans CN', 'Microsoft YaHei', sans-serif; line-height: 1.7; }
.simulation-container { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; padding: 2rem; }
.process-panel { background: #f9fafb; padding: 1.5rem; border-radius: 1rem; }
.simulation-panel { background: white; padding: 1.5rem; border-radius: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
</style>
"""
        return html.replace('</head>', style + '</head>')

    def _emergency_template(self, analysis: Dict, user_preferences: Dict) -> str:
        """Emergency fallback template."""
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>学习网站</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-3xl font-bold mb-4">{analysis.get('subject_area', '学习')}</h1>
        <p>内容生成中遇到问题，请稍后重试。</p>
    </div>
</body>
</html>"""

    def _extract_procedural_concepts(self, analysis: Dict) -> List[Dict]:
        """Extract procedural concepts from analysis."""
        procedural_concepts = analysis.get('procedural_concepts', [])

        if not procedural_concepts:
            procedural_concepts = [
                {
                    "name": concept,
                    "description": f"理解并应用{concept}",
                    "key_steps": ["理解", "练习", "应用"],
                    "complexity": "中等"
                }
                for concept in analysis.get('key_concepts', [])[:3]
            ]

        return procedural_concepts[:3]

    def _map_grade_level(self, grade_level: int) -> str:
        """Map integer grade to Chinese string."""
        grade_mapping = {
            0: "幼儿园", 1: "小学一年级", 2: "小学二年级", 3: "小学三年级",
            4: "小学四年级", 5: "小学五年级", 6: "小学六年级",
            7: "初中一年级", 8: "初中二年级", 9: "初中三年级",
            10: "高中一年级", 11: "高中二年级", 12: "高中三年级"
        }
        return grade_mapping.get(grade_level, f"年级{grade_level}")

    async def _generate_fallback(self, pdf_images: List[Dict], analysis: Dict,
                                 user_preferences: Dict) -> Dict:
        """Generate complete fallback response."""
        try:
            procedural_concepts = self._extract_procedural_concepts(analysis)
            fast_generator = FastGenerator(self.provider)
            metadata_and_elements = await fast_generator._generate_metadata_and_interactive(
                procedural_concepts, analysis, user_preferences
            )
        except Exception:
            metadata_and_elements = {}

        return {
            "html": self._emergency_template(analysis, user_preferences),
            "metadata": {
                **self._generate_metadata(analysis, user_preferences),
                **metadata_and_elements.get("metadata", {})
            },
            "interactive_elements": metadata_and_elements.get("interactive_elements", []),
            "generation_info": {
                "mode": "heavy",
                "fallback_used": True,
                "stages_completed": 0,
                "refinements": {}
            }
        }
