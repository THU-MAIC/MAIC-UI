"""
PPT Processor Service - Consolidated module for PPT/PPTX/PDF to interactive slides conversion.

This module contains three main classes:
1. PPTImageConverter: Handles file conversions to images
2. PPTDemoAnalyzer: Analyzes slides and generates demo content
3. PPTProcessor: Main orchestrator for the entire pipeline
"""

import os
import subprocess
import json
import time
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Model to provider mapping
CHINESE_MODELS = ["claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5-20251001",
                  "glm-4.7", "glm-4.6", "glm-4.6v"]


def get_provider_for_model(model: str) -> str:
    """
    Determine the provider type based on the model name.

    Args:
        model: Model name

    Returns:
        Provider type: "chinese" or "english"
    """
    if model in CHINESE_MODELS:
        return "chinese"
    return "english"


def get_ai_processor(generation_mode: str = "fast", ai_model: Optional[str] = None):
    """
    Get AI processor instance based on configuration.

    Args:
        generation_mode: HTML generation mode ("fast" or "heavy")
        ai_model: Specific model to use. If provided, provider is inferred from model name.

    Returns:
        AIProcessor instance
    """
    from .ai_processor import AIProcessor

    # If a specific model is provided, infer provider from model
    if ai_model:
        provider_type = get_provider_for_model(ai_model)
        logger.info(f"Using model {ai_model} with inferred provider: {provider_type}")
    else:
        provider_type = os.getenv('AI_PROVIDER', 'chinese').lower()

    # Set model and API key based on provider type
    if provider_type in ['english', 'gemini', 'openai']:
        if provider_type == 'gemini':
            model = ai_model or os.getenv('GEMINI_MODEL', 'gemini-3-pro-image-preview')
            api_key = os.getenv('GEMINI_API_KEY') or os.getenv('ENGLISH_API_KEY') or os.getenv('MIDDLE_TRANSFER_API_KEY')
        elif provider_type == 'openai':
            model = ai_model or os.getenv('OPENAI_MODEL', 'gpt-4.1')
            api_key = os.getenv('OPENAI_API_KEY') or os.getenv('ENGLISH_API_KEY') or os.getenv('MIDDLE_TRANSFER_API_KEY')
        else:  # english (default)
            model = ai_model or os.getenv('ENGLISH_MODEL', 'gpt-4.1')
            api_key = os.getenv('ENGLISH_API_KEY') or os.getenv('MIDDLE_TRANSFER_API_KEY') or os.getenv('OPENAI_API_KEY') or os.getenv('GEMINI_API_KEY')

        provider_config = {
            'provider': 'english',  # Always use unified English provider
            'model': model,
            'api_key': api_key
        }
    elif provider_type == 'chinese':
        # Unified Chinese provider - auto-detect backend from model name
        if ai_model and ai_model.startswith('claude-'):
            # Anthropic model
            model = ai_model
            api_key = os.getenv('ANTHROPIC_API_KEY')
            base_url = os.getenv('ANTHROPIC_BASE_URL')
        else:
            # Zhipu model (default)
            model = 'glm-4.6v'  # Vision model for slide analysis
            api_key = os.getenv('ZHIPU_API_KEY')
            base_url = None

        text_model = ai_model if ai_model in CHINESE_MODELS else os.getenv('ZHIPU_MODEL', 'glm-4.7')
        provider_config = {
            'provider': 'chinese',
            'model': model,
            'api_key': api_key,
            'base_url': base_url,
            'text_model': text_model
        }
    else:
        raise ValueError(f"Unsupported provider: {provider_type}. Supported providers: english, chinese")

    return AIProcessor(provider_config=provider_config, generation_mode=generation_mode)

# Import PyMuPDF for PDF processing
try:
    import fitz  # PyMuPDF is imported as fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.error("PyMuPDF (fitz) not available. Install with: pip install PyMuPDF")


class PPTImageConverter:
    """Handle PPT/PPTX/PDF to image conversion."""

    def __init__(self):
        self.upload_dir = Path("uploads/ppt")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def convert_pptx_to_pdf(self, pptx_path: str) -> str:
        """
        Convert .pptx file to .pdf using LibreOffice.

        Args:
            pptx_path: Path to the PPTX file

        Returns:
            Path to the converted PDF file

        Raises:
            RuntimeError: If LibreOffice is not available or conversion fails
        """
        try:
            pptx_file = Path(pptx_path)
            pdf_path = pptx_file.parent / f"{pptx_file.stem}.pdf"

            # Try LibreOffice conversion
            logger.info(f"Converting PPTX to PDF using LibreOffice: {pptx_path}")

            # Set environment to ensure proper font rendering
            import os as os_module
            env = os_module.environ.copy()
            env['LANG'] = 'C.UTF-8'
            env['DISPLAY'] = ':0'  # Required for LibreOffice font rendering

            # Try different LibreOffice commands
            commands = [
                ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', str(pptx_file.parent), str(pptx_path)],
                ['soffice', '--headless', '--convert-to', 'pdf', '--outdir', str(pptx_file.parent), str(pptx_path)],
                ['/usr/lib/libreoffice/program/soffice', '--headless', '--convert-to', 'pdf', '--outdir', str(pptx_file.parent), str(pptx_path)]
            ]

            for cmd in commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=60,
                        env=env
                    )
                    if result.returncode == 0 and pdf_path.exists():
                        logger.info(f"Successfully converted PPTX to PDF: {pdf_path}")
                        return str(pdf_path)
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue

            # If LibreOffice not available, raise error
            raise RuntimeError(
                "LibreOffice not found. Please install LibreOffice or convert PPTX to PDF manually. "
                "Alternatively, upload PDF files directly."
            )

        except Exception as e:
            logger.error(f"Error converting PPTX to PDF: {e}")
            raise

    def convert_pdf_to_slide_images(
        self,
        pdf_path: str,
        output_dir: str,
        zoom: float = 2.0,
        image_format: str = "png"
    ) -> List[str]:
        """
        Convert PDF pages to images using PyMuPDF.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save slide images
            zoom: Zoom factor for image quality (default 2.0 for high quality)
            image_format: Image format ('png' or 'jpg')

        Returns:
            List of paths to generated slide images
        """
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF (fitz) not available. Install with: pip install PyMuPDF")

        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            doc = fitz.open(pdf_path)
            slide_paths = []

            logger.info(f"Converting PDF to images: {pdf_path} ({len(doc)} pages)")

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Create transformation matrix for zoom
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)

                # Save image
                image_filename = f"slide_{page_num + 1}.{image_format}"
                image_path = output_path / image_filename

                if image_format == "png":
                    pix.save(str(image_path))
                elif image_format == "jpg":
                    pix.save(str(image_path), jpeg_quality=95)
                else:
                    raise ValueError(f"Unsupported image format: {image_format}")

                slide_paths.append(str(image_path))
                logger.debug(f"Saved slide {page_num + 1}: {image_path}")

            doc.close()
            logger.info(f"Successfully converted {len(slide_paths)} slides to images")

            return slide_paths

        except Exception as e:
            logger.error(f"Error converting PDF to slide images: {e}")
            raise

    def save_slide_images(self, images: List[Any], document_id: int) -> List[str]:
        """
        Save PIL Image objects to disk.

        Args:
            images: List of PIL Image objects
            document_id: Document ID for organizing files

        Returns:
            List of saved image paths
        """
        try:
            doc_dir = self.upload_dir / str(document_id) / "slides"
            doc_dir.mkdir(parents=True, exist_ok=True)

            saved_paths = []
            for idx, image in enumerate(images):
                image_path = doc_dir / f"slide_{idx + 1}.png"
                image.save(str(image_path), "PNG")
                saved_paths.append(str(image_path))

            logger.info(f"Saved {len(saved_paths)} slide images for document {document_id}")
            return saved_paths

        except Exception as e:
            logger.error(f"Error saving slide images: {e}")
            raise


class PPTDemoAnalyzer:
    """Handle AI analysis for demo insertion points and HTML generation."""

    def __init__(self, ai_provider, db_session_factory=None):
        """
        Initialize analyzer with an AI provider.

        Args:
            ai_provider: Instance of AIProvider (e.g., ZhipuProvider)
            db_session_factory: Optional function to create DB sessions for template search
        """
        self.ai_provider = ai_provider
        self.db_session_factory = db_session_factory

    async def analyze_slides_for_demo_opportunities(
        self,
        slide_images: List[str],
        user_preferences: Dict,
        processing_config: Optional[Dict] = None
    ) -> Dict:
        """
        Use AI to analyze which slides need interactive demos.

        Args:
            slide_images: List of paths to slide images
            user_preferences: User preferences (grade_level, interests, etc.)
            processing_config: Optional processing configuration
                {
                    "mode": "batch" | "specific_pages",
                    "batch_size": 5,  # for batch mode
                    "selected_pages": [1, 3, 5],  # for specific_pages mode
                }

        Returns:
            Analysis results with demo insertion recommendations
        """
        logger.info(f"Analyzing {len(slide_images)} slides for demo opportunities")
        logger.info(f"Processing config: {processing_config}")

        try:
            # Determine which slides to analyze
            slides_to_analyze = list(range(1, len(slide_images) + 1))

            if processing_config:
                mode = processing_config.get("mode", "batch")

                if mode == "specific_pages":
                    # Only analyze selected pages
                    selected = processing_config.get("selected_pages", [])
                    # Validate page numbers
                    slides_to_analyze = [p for p in selected if 1 <= p <= len(slide_images)]
                    logger.info(f"Specific pages mode: analyzing pages {slides_to_analyze}")

            # Process slides in batches to avoid token limits
            batch_size = 1  # Default batch size

            if processing_config and processing_config.get("mode") == "batch":
                batch_size = processing_config.get("batch_size", 5)
                logger.info(f"Using custom batch size: {batch_size}")

            all_slides = []

            for batch_start in range(0, len(slides_to_analyze), batch_size):
                batch_end = min(batch_start + batch_size, len(slides_to_analyze))
                batch_page_numbers = slides_to_analyze[batch_start:batch_end]
                batch_images = [slide_images[p - 1] for p in batch_page_numbers]  # Convert to 0-indexed

                logger.info(f"Processing batch {batch_start//batch_size + 1}: slides {batch_page_numbers}")

                # Convert image paths to base64 for AI processing
                slide_data = []
                for idx, img_path in enumerate(batch_images):
                    slide_number = batch_page_numbers[idx]
                    try:
                        # Compress image by resizing before encoding
                        from PIL import Image
                        import base64
                        import io

                        img = Image.open(img_path)
                        # Resize to max 800x600 for smaller payload
                        img.thumbnail((800, 600), Image.Resampling.LANCZOS)

                        buffer = io.BytesIO()
                        img.save(buffer, format="JPEG", quality=70)  # Use JPEG with compression
                        img_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

                        slide_data.append({
                            "slide_number": slide_number,
                            "image_data": f"data:image/jpeg;base64,{img_data}"
                        })
                    except Exception as e:
                        logger.warning(f"Failed to process slide {slide_number}: {e}")

                if not slide_data:
                    continue

                # Prepare analysis prompt for this batch
                grade_level = user_preferences.get('grade_level', 10)
                subject = user_preferences.get('subject', 'Unknown')

                # Determine which prompt to use based on processing mode
                is_specific_pages_mode = processing_config and processing_config.get("mode") == "specific_pages"

                if is_specific_pages_mode:
                    # For specific pages mode, tell AI exactly which slide numbers it's analyzing
                    actual_slide_numbers = [sd["slide_number"] for sd in slide_data]
                    prompt = self._get_specific_pages_analysis_prompt(grade_level, subject, actual_slide_numbers)
                else:
                    # For batch mode, use sequential numbering starting from batch_start
                    prompt = self._get_batch_analysis_prompt(grade_level, subject)

                # Build content list for AI
                content = [{"type": "text", "text": prompt}]
                for slide in slide_data:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": slide["image_data"]}
                    })

                # Call AI provider
                response = await self._call_ai_for_analysis(content)

                # Extract slides from response and add to all_slides
                if 'slides' in response:
                    response_slides = response['slides']

                    # For specific_pages mode, the AI should return correct slide_numbers
                    # For batch mode, the AI returns sequential numbers (1, 2, 3...) that need to be mapped to actual slide numbers
                    if is_specific_pages_mode:
                        # AI should have used the actual slide numbers we provided
                        # Verify and correct if needed
                        for i, slide in enumerate(response_slides):
                            if i < len(batch_page_numbers):
                                expected_slide_number = batch_page_numbers[i]
                                if slide.get('slide_number') != expected_slide_number:
                                    logger.warning(f"AI returned slide_number {slide.get('slide_number')} but expected {expected_slide_number}. Correcting...")
                                    slide['slide_number'] = expected_slide_number
                        all_slides.extend(response_slides)
                    else:
                        # Batch mode: Map sequential numbers to actual slide numbers
                        for i, slide in enumerate(response_slides):
                            if i < len(batch_page_numbers):
                                # Replace AI's sequential number with actual slide number
                                slide['slide_number'] = batch_page_numbers[i]
                        all_slides.extend(response_slides)
                else:
                    logger.warning(f"No slides in response for batch {batch_start//batch_size + 1}")

            # Compile final analysis
            return {
                "overall_topic": "Presentation Analysis",
                "target_audience": f"Grade {user_preferences.get('grade_level', 10)} Students",
                "key_concepts": [],
                "slides": all_slides
            }

        except Exception as e:
            logger.error(f"Error analyzing slides for demo opportunities: {e}")
            # Return fallback analysis
            return self._get_fallback_analysis(len(slide_images))

    def _get_slide_analysis_prompt(self, grade_level: int, subject: str) -> str:
        """生成幻灯片分析的提示词。"""
        return f"""请分析这些演示文稿幻灯片，并确定在哪里添加交互式演示可以帮助学生理解内容。

上下文：
- 年级水平: {grade_level}
- 学科: {subject}

对于每张幻灯片，请确定：
1. 这张幻灯片是否引入了需要交互式演示帮助理解的复杂概念？
2. 什么类型的演示最有帮助？
3. 为什么这张幻灯片需要演示？

演示类型包括：
- simulation: 交互式模拟或模型
- visualization: 数据可视化或图表
- practice: 练习或测验
- experiment: 虚拟实验或实验室

请以JSON格式回复：
{{
  "overall_topic": "演示文稿的主要主题",
  "target_audience": "目标受众描述",
  "key_concepts": ["概念1", "概念2"],
  "slides": [
    {{
      "slide_number": 1,
      "title": "幻灯片标题",
      "description": "幻灯片内容的简要描述",
      "needs_demo": false,
      "reason": "不需要 - 内容直观易懂"
    }},
    {{
      "slide_number": 2,
      "title": "复杂算法",
      "description": "复杂概念的描述",
      "needs_demo": true,
      "reason": "复杂算法需要逐步可视化",
      "demo_type": "simulation"
    }}
  ]
}}"""

    def _get_batch_analysis_prompt(self, grade_level: int, subject: str) -> str:
        """为批量处理模式生成分析提示词。幻灯片按批次顺序编号。"""
        return f"""请分析这些演示文稿幻灯片，并确定在哪里添加交互式演示可以帮助学生理解内容。

上下文：
- 年级水平: {grade_level}
- 学科: {subject}
- 处理模式：批量处理（按顺序处理所有幻灯片）

对于每张幻灯片，请确定：
1. 这张幻灯片是否引入了需要交互式演示帮助理解的复杂概念？
2. 什么类型的演示最有帮助？
3. 为什么这张幻灯片需要演示？

演示类型包括：
- simulation: 交互式模拟或模型
- visualization: 数据可视化或图表
- practice: 练习或测验
- experiment: 虚拟实验或实验室

请以JSON格式回复，按图片顺序将幻灯片编号为1、2、3...：
{{
  "overall_topic": "演示文稿的主要主题",
  "target_audience": "目标受众描述",
  "key_concepts": ["概念1", "概念2"],
  "slides": [
    {{
      "slide_number": 1,
      "title": "幻灯片标题",
      "description": "幻灯片内容的简要描述",
      "needs_demo": false,
      "reason": "不需要 - 内容直观易懂"
    }},
    {{
      "slide_number": 2,
      "title": "复杂算法",
      "description": "复杂概念的描述",
      "needs_demo": true,
      "reason": "复杂算法需要逐步可视化",
      "demo_type": "simulation"
    }}
  ]
}}"""

    def _get_specific_pages_analysis_prompt(self, grade_level: int, subject: str, actual_slide_numbers: List[int]) -> str:
        """为指定页面模式生成分析提示词。明确告诉AI正在分析哪些幻灯片编号。"""
        slides_text = ", ".join(map(str, actual_slide_numbers))
        return f"""请分析这些演示文稿幻灯片，并确定在哪里添加交互式演示可以帮助学生理解内容。

上下文：
- 年级水平: {grade_level}
- 学科: {subject}
- 处理模式：指定页面分析

重要：您正在分析以下特定的幻灯片编号（按图片顺序）：{slides_text}

请在返回的 JSON 中使用这些确切的幻灯片编号，不要从1开始重新编号！

例如，如果图片顺序对应幻灯片 {actual_slide_numbers[0] if actual_slide_numbers else 14}, {actual_slide_numbers[1] if len(actual_slide_numbers) > 1 else 19}，则 JSON 应为：
{{
  "slides": [
    {{
      "slide_number": {actual_slide_numbers[0] if actual_slide_numbers else 14},
      ...
    }},
    {{
      "slide_number": {actual_slide_numbers[1] if len(actual_slide_numbers) > 1 else 19},
      ...
    }}
  ]
}}

演示类型包括：
- simulation: 交互式模拟或模型
- visualization: 数据可视化或图表
- practice: 练习或测验
- experiment: 虚拟实验或实验室

请以JSON格式回复：
{{
  "overall_topic": "演示文稿的主要主题",
  "target_audience": "目标受众描述",
  "key_concepts": ["概念1", "概念2"],
  "slides": [
    {{
      "slide_number": <使用实际的幻灯片编号>,
      "title": "幻灯片标题",
      "description": "幻灯片内容的简要描述",
      "needs_demo": false,
      "reason": "不需要 - 内容直观易懂"
    }}
  ]
}}"""

    async def _call_ai_for_analysis(self, content: List[Dict]) -> Dict:
        """Call AI provider for slide analysis."""
        try:
            # Get the actual provider (might be wrapped in AIProcessor)
            actual_provider = self.ai_provider
            if hasattr(self.ai_provider, 'provider'):
                actual_provider = self.ai_provider.provider

            content_text = None

            # Determine which API to use based on model name (not just method existence)
            model = getattr(actual_provider, 'model', '')
            is_anthropic_model = model.startswith('claude-')

            # Use Anthropic if it's a Claude model, otherwise use Zhipu
            if is_anthropic_model and hasattr(actual_provider, '_run_anthropic_call'):
                # Anthropic provider
                model = getattr(actual_provider, 'model', 'claude-sonnet-4-6')
                logger.info(f"Calling Anthropic AI for slide analysis with model {model}")

                # Convert content format for Anthropic (text and images)
                anthropic_content = []
                for item in content:
                    if item.get("type") == "text":
                        anthropic_content.append({"type": "text", "text": item["text"]})
                    elif item.get("type") == "image_url":
                        # Extract base64 data from data URL
                        image_url = item["image_url"]["url"]
                        if image_url.startswith("data:"):
                            # Parse data URL: data:image/jpeg;base64,<data>
                            parts = image_url.split(",", 1)
                            if len(parts) == 2:
                                media_type = parts[0].replace("data:", "").replace(";base64", "")
                                anthropic_content.append({
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": parts[1]
                                    }
                                })

                response = await actual_provider._run_anthropic_call(
                    model=model,
                    messages=[{"role": "user", "content": anthropic_content}],
                    max_tokens=4096,
                    thinking_enabled=False
                )

                if response and response.content:
                    for block in response.content:
                        if hasattr(block, 'text'):
                            content_text = block.text
                            break

            elif hasattr(actual_provider, '_run_zhipu_call'):
                # Zhipu provider (non-Anthropic models)
                logger.info(f"Calling Zhipu AI for slide analysis with model {actual_provider.model}")
                response = await actual_provider._run_zhipu_call(
                    model=actual_provider.model,
                    messages=[{"role": "user", "content": content}],
                    thinking_params={"type": "disabled"}
                )

                if response and response.choices and response.choices[0].message:
                    content_text = response.choices[0].message.content

            if content_text:
                logger.info(f"Received AI response, length: {len(content_text)}")
                # Extract JSON
                json_start = content_text.find('{')
                json_end = content_text.rfind('}') + 1

                if json_start != -1 and json_end > json_start:
                    json_str = content_text[json_start:json_end]
                    return json.loads(json_str)
                else:
                    logger.warning(f"No valid JSON found in AI response")

            # Fallback
            logger.warning("AI provider not supported or call failed, using fallback analysis")
            return self._get_fallback_analysis(10)

        except Exception as e:
            logger.error(f"Error calling AI for analysis: {e}", exc_info=True)
            return self._get_fallback_analysis(10)

    def _get_fallback_analysis(self, num_slides: int) -> Dict:
        """Return fallback analysis when AI fails."""
        return {
            "overall_topic": "Presentation",
            "target_audience": "Students",
            "key_concepts": [],
            "slides": [
                {
                    "slide_number": i + 1,
                    "title": f"Slide {i + 1}",
                    "description": "Slide content",
                    "needs_demo": False,
                    "reason": "Analysis not available"
                }
                for i in range(num_slides)
            ]
        }

    async def search_templates_for_slides(
        self,
        slides_needing_demos: List[Dict],
        user_preferences: Dict,
        max_results_per_slide: int = 3
    ) -> Dict[int, List[Dict]]:
        """
        Search for templates matching slides that need demos.

        Args:
            slides_needing_demos: List of slide info dicts that need demos
            user_preferences: User preferences (grade_level, interests, etc.)
            max_results_per_slide: Maximum template options per slide

        Returns:
            Dict mapping slide_number to list of template options
            {
                2: [
                    {
                        "template_id": "sorting_visualization",
                        "display_name": "排序算法可视化",
                        "match_score": 0.85,
                        "match_reason": "..."
                    },
                    ...
                ],
                ...
            }
        """
        if not self.db_session_factory:
            logger.error("=" * 80)
            logger.error("TEMPLATE SEARCH FAILED: No database session factory available")
            logger.error("=" * 80)
            return {}

        # Get ai_model from user_preferences if available
        ai_model = user_preferences.get("ai_model") or user_preferences.get("zhipu_text_model")

        # Use local get_ai_processor for proper provider selection
        ai_processor = get_ai_processor(ai_model=ai_model)
        logger.info(f"🤖 Template search using provider: {ai_processor.get_provider_name()}, model: {ai_model or 'default'}")
        template_options_by_slide = {}

        logger.info(f"Searching templates for {len(slides_needing_demos)} slides")

        for slide_info in slides_needing_demos:
            slide_number = slide_info.get('slide_number')

            # Build content info for template search
            content_info = {
                "title": slide_info.get('title', ''),
                "description": slide_info.get('description', ''),
                "demo_type": slide_info.get('demo_type', 'visualization'),
                "grade_level": user_preferences.get('grade_level', 6),
                "subject": user_preferences.get('subject', '')
            }

            logger.info(f"Content info for template search: {content_info}")

            try:
                # Search templates using AI processor
                logger.info(f"Calling ai_processor.search_templates_for_user...")
                result = await ai_processor.search_templates_for_user(
                    content_info=content_info,
                    workflow_type="ppt_demo",
                    db_session_factory=self.db_session_factory,
                    max_results=max_results_per_slide
                )

                logger.info(f"Template search result status: {result.get('status')}")
                logger.info(f"Templates found: {result.get('templates_found', 0)}")

                if result.get('status') == 'success' and result.get('template_options'):
                    template_options_by_slide[slide_number] = result['template_options']
                    logger.info(f"✅ Found {len(result['template_options'])} templates for slide {slide_number}")
                    for opt in result['template_options']:
                        logger.info(f"    - {opt.get('display_name')} (match: {opt.get('match_score', 0):.2f})")
                else:
                    logger.warning(f"❌ No templates found for slide {slide_number}")
                    logger.warning(f"Result: {result}")

            except Exception as e:
                logger.error(f"❌ Error searching templates for slide {slide_number}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Continue with next slide

        logger.info(f"-" * 80)
        logger.info(f"Template search completed for all slides")
        logger.info(f"Total slides with templates: {len(template_options_by_slide)}")

        return template_options_by_slide

    async def generate_demo_html(
        self,
        slide_image_path: str,
        slide_info: Dict,
        user_preferences: Dict
    ) -> str:
        """
        Generate interactive HTML demo for a specific slide.

        Args:
            slide_image_path: Path to slide image
            slide_info: Slide metadata from analysis
            user_preferences: User preferences

        Returns:
            Generated HTML demo content
        """
        logger.info(f"Generating demo HTML for slide {slide_info.get('slide_number')}")

        try:
            # Prepare generation prompt (text-only, no image)
            prompt = self._get_demo_generation_prompt(slide_info, user_preferences)

            # Call AI to generate demo using text model
            html_content = await self._call_ai_for_demo_generation(prompt)

            return html_content

        except Exception as e:
            logger.error(f"Error generating demo HTML: {e}")
            return self._get_fallback_demo_html(slide_info)

    async def generate_demo_html_with_template(
        self,
        slide_info: Dict,
        user_preferences: Dict,
        template_id: str,
        customization_params: Optional[Dict] = None
    ) -> str:
        """
        Generate interactive HTML demo for a specific slide using a selected template.

        Args:
            slide_info: Slide metadata from analysis
            user_preferences: User preferences
            template_id: ID of the template to use
            customization_params: Optional customization parameters

        Returns:
            Generated HTML demo content using the template
        """
        slide_number = slide_info.get('slide_number')
        logger.info(f"=" * 80)
        logger.info(f"GENERATING DEMO WITH TEMPLATE")
        logger.info(f"Slide: {slide_number}")
        logger.info(f"Template ID: {template_id}")
        logger.info(f"=" * 80)

        if not self.db_session_factory:
            logger.error("No database session factory available, falling back to AI-only generation")
            return await self.generate_demo_html("", slide_info, user_preferences)

        try:
            # Get ai_model from user_preferences if available
            ai_model = user_preferences.get("ai_model") or user_preferences.get("zhipu_text_model")

            logger.info(f"Getting AI processor with model: {ai_model or 'default'}...")
            # Use local get_ai_processor for proper provider selection
            ai_processor = get_ai_processor(ai_model=ai_model)
            logger.info(f"🤖 Demo generation using provider: {ai_processor.get_provider_name()}")

            # Build content info for template customization
            content_info = {
                "title": slide_info.get('title', ''),
                "description": slide_info.get('description', ''),
                "demo_type": slide_info.get('demo_type', 'visualization'),
                "reason": slide_info.get('reason', ''),
                "grade_level": user_preferences.get('grade_level', 6),
                "subject": user_preferences.get('subject', '')
            }

            logger.info(f"Content info for template generation: {content_info}")
            logger.info(f"Calling ai_processor.generate_with_selected_template...")

            # Generate using selected template
            result = await ai_processor.generate_with_selected_template(
                template_id=template_id,
                content_info=content_info,
                user_preferences=user_preferences,
                workflow_type="ppt_demo",
                db_session_factory=self.db_session_factory,
                customization_params=customization_params
            )

            if result.get('status') == 'success' and result.get('html'):
                logger.info(f"✅ Successfully generated demo for slide {slide_number} using template {template_id}")
                return result['html']
            else:
                logger.warning(f"❌ Template generation failed for slide {slide_number}, falling back to AI-only")
                logger.warning(f"Result: {result}")
                return await self.generate_demo_html("", slide_info, user_preferences)

        except Exception as e:
            logger.error(f"❌ Error generating demo with template: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Fallback to regular generation
            return await self.generate_demo_html("", slide_info, user_preferences)

    def _get_demo_generation_prompt(self, slide_info: Dict, user_preferences: Dict) -> str:
        """为演示HTML生成生成提示词。"""
        demo_type = slide_info.get('demo_type', 'visualization')
        reason = slide_info.get('reason', '')
        title = slide_info.get('title', '未知标题')
        description = slide_info.get('description', '')
        grade_level = user_preferences.get('grade_level', 6)

        return f"""请创建一个交互式HTML演示，帮助学生理解这个演示文稿幻灯片的内容。

幻灯片信息：
- 标题: {title}
- 描述: {description}
- 需要的演示类型: {demo_type}
- 原因: {reason}

学生年级: {grade_level}年级

要求：
1. 创建一个独立的HTML页面，包含嵌入的CSS和JavaScript
2. 使其对学生具有互动性和吸引力
3. 根据需要包含视觉元素、动画或模拟
4. 确保演示直接帮助理解幻灯片的内容
5. 使用现代、简洁的设计和响应式布局
6. 包含指导学生的说明文字
7. 在相关位置添加交互控件（按钮、滑块、输入框）

演示应该：
- 具有教育意义且适合该年龄段
- 强化幻灯片中的关键概念
- 允许学生探索和实验
- 提供即时反馈
- 在浏览器中独立运行

请只返回完整的HTML代码（不要使用markdown格式）。"""

    async def _call_ai_for_demo_generation(self, prompt: str) -> str:
        """调用AI提供商生成演示HTML。"""
        try:
            # Get the actual provider (might be wrapped in AIProcessor)
            actual_provider = self.ai_provider
            if hasattr(self.ai_provider, 'provider'):
                actual_provider = self.ai_provider.provider

            content_text = None

            # Determine which API to use based on model name (not just method existence)
            model = getattr(actual_provider, 'model', '')
            is_anthropic_model = model.startswith('claude-')

            # Use Anthropic if it's a Claude model, otherwise use Zhipu
            if is_anthropic_model and hasattr(actual_provider, '_run_anthropic_call'):
                # Anthropic provider
                logger.info(f"调用Anthropic AI生成演示HTML，使用模型 {model}")

                response = await actual_provider._run_anthropic_call(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    thinking_enabled=True  # Enable extended thinking for complex HTML generation
                )

                if response and response.content:
                    for block in response.content:
                        if hasattr(block, 'text'):
                            content_text = block.text
                            break

            elif hasattr(actual_provider, '_run_zhipu_call'):
                # Zhipu provider (non-Anthropic models)
                text_model = getattr(actual_provider, 'text_model', 'glm-4.7')
                logger.info(f"调用智谱AI生成演示HTML，使用模型 {text_model}")
                response = await actual_provider._run_zhipu_call(
                    model=text_model,  # 使用文本模型生成HTML
                    messages=[{"role": "user", "content": prompt}],
                    thinking_params={"type": "enabled"},  # 启用深度思考以生成复杂HTML
                )

                if response and response.choices and response.choices[0].message:
                    content_text = response.choices[0].message.content

            if content_text:
                logger.info(f"收到AI HTML响应，长度: {len(content_text)}")

                # Extract HTML from response - look for HTML tags
                html_start = content_text.find('<!DOCTYPE html>')
                if html_start == -1:
                    html_start = content_text.find('<html')

                html_end_index = content_text.rfind('</html>')
                html_end = html_end_index + len('</html>') if html_end_index != -1 else -1

                if html_start != -1 and html_end > html_start:
                    return content_text[html_start:html_end]
                elif html_start != -1:
                    # No closing tag found, return from start to end (after cleaning markdown)
                    content_text = content_text.replace('```html', '').replace('```', '')
                    return content_text[html_start:].strip()
                else:
                    # Clean up markdown if present
                    content_text = content_text.replace('```html', '').replace('```', '')
                    return content_text.strip()

            logger.warning("AI提供商不支持演示生成，使用后备方案")
            return self._get_fallback_demo_html({})

        except Exception as e:
            logger.error(f"调用AI生成演示时出错: {e}", exc_info=True)
            return self._get_fallback_demo_html({})

    def _get_fallback_demo_html(self, slide_info: Dict) -> str:
        """Return fallback demo HTML when generation fails."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Demo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .demo-container {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .content {
            margin: 20px 0;
            padding: 20px;
            background: #f5f5f5;
            border-radius: 5px;
        }
        .interactive {
            margin: 20px 0;
            padding: 20px;
            background: #e3f2fd;
            border-radius: 5px;
            text-align: center;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 5px;
        }
        button:hover {
            background: #5568d3;
        }
        #output {
            margin-top: 20px;
            padding: 15px;
            background: white;
            border-radius: 5px;
            min-height: 50px;
        }
    </style>
</head>
<body>
    <div class="demo-container">
        <h1>Interactive Demo</h1>
        <div class="content">
            <p>This demo helps visualize the concepts from the presentation.</p>
        </div>
        <div class="interactive">
            <button onclick="showDemo()">Click to Interact</button>
            <button onclick="resetDemo()">Reset</button>
            <div id="output"></div>
        </div>
    </div>
    <script>
        function showDemo() {
            const output = document.getElementById('output');
            output.innerHTML = '<p style="color: #667eea; font-size: 18px;">Great! You\'re interacting with the demo. This helps reinforce learning through hands-on engagement.</p>';
        }
        function resetDemo() {
            const output = document.getElementById('output');
            output.innerHTML = '';
        }
    </script>
</body>
</html>"""


class PPTProcessor:
    """Main orchestrator for PPT processing pipeline."""

    def __init__(self, ai_provider=None, db_session_factory=None):
        """
        Initialize PPT processor.

        Args:
            ai_provider: Optional AI provider instance (will create default if not provided)
            db_session_factory: Optional function to create DB sessions for template operations
        """
        self.image_converter = PPTImageConverter()
        self.ai_provider = ai_provider
        self.db_session_factory = db_session_factory
        self.demo_analyzer = None

        if ai_provider:
            self.demo_analyzer = PPTDemoAnalyzer(ai_provider, db_session_factory)

    def process_file(self, file_path: str, file_type: str, document_id: int) -> Tuple[List[str], str]:
        """
        Process uploaded file (PPTX or PDF) and convert to slide images.

        Args:
            file_path: Path to uploaded file
            file_type: Type of file ('pptx' or 'pdf')
            document_id: Document ID for organizing output

        Returns:
            Tuple of (list of slide image paths, PDF path used)
        """
        logger.info(f"Processing {file_type} file: {file_path}")

        # Convert PPTX to PDF if needed
        if file_type == 'pptx':
            pdf_path = self.image_converter.convert_pptx_to_pdf(file_path)
        else:
            pdf_path = file_path

        # Convert PDF to slide images
        output_dir = f"uploads/ppt/{document_id}/slides"
        slide_paths = self.image_converter.convert_pdf_to_slide_images(pdf_path, output_dir)

        logger.info(f"Successfully processed {len(slide_paths)} slides")
        return slide_paths, pdf_path

    def get_file_info(self, file_path: str) -> Dict:
        """
        Get metadata about uploaded file.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file metadata
        """
        path = Path(file_path)
        return {
            "filename": path.name,
            "size": path.stat().st_size if path.exists() else 0,
            "extension": path.suffix.lower()
        }


async def process_ppt_background(
    document_id: int,
    file_path: str,
    file_type: str,
    user_prefs: Dict,
    db_session_factory
):
    """
    Background task to process PPT/PPTX/PDF asynchronously.

    Args:
        document_id: ID of the PPTDocument
        file_path: Path to uploaded file
        file_type: Type of file ('pptx' or 'pdf')
        user_prefs: User preferences
        db_session_factory: Function to create new DB sessions
    """
    logger.info(f"Starting background PPT processing for document {document_id}")
    start_time = time.time()

    # Create new database session
    db = db_session_factory()

    try:
        from ..models.ppt_document import PPTDocument

        # Get document
        document = db.query(PPTDocument).filter(PPTDocument.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            return

        # Get processing config from document
        processing_config = document.processing_config or {}
        logger.info(f"Using processing config: {processing_config}")

        # Check if template workflow is enabled
        use_templates = processing_config.get('use_templates', True)
        logger.info(f"Template workflow: {'enabled' if use_templates else 'disabled'}")

        # Get ai_model from user preferences or processing_config
        # Priority: user_prefs > processing_config
        selected_model = (
            user_prefs.get("ai_model") or
            user_prefs.get("zhipu_text_model") or
            processing_config.get("ai_model") or
            processing_config.get("zhipu_text_model")
        )

        # Use local get_ai_processor function for proper provider selection
        ai_processor = get_ai_processor(ai_model=selected_model)
        logger.info(f"🤖 AI processor initialized - Provider: {ai_processor.get_provider_name()}, Model: {selected_model or 'default'}")

        # For Zhipu provider, also set the text_model attribute for compatibility
        if selected_model and hasattr(ai_processor.provider, 'text_model'):
            ai_processor.provider.text_model = selected_model
            logger.info(f"🔄 Set AI Model: {selected_model}")

        processor = PPTProcessor(ai_provider=ai_processor, db_session_factory=db_session_factory)

        # Convert file to slide images
        logger.info(f"Converting {file_type} to slides...")
        slide_paths, pdf_used = processor.process_file(file_path, file_type, document_id)

        # Analyze slides for demo opportunities
        logger.info("Analyzing slides for demo opportunities...")
        analysis = await processor.demo_analyzer.analyze_slides_for_demo_opportunities(
            slide_paths,
            user_prefs,
            processing_config
        )

        # Build slides data - include ALL slides, not just analyzed ones
        # Create a map of analyzed slides by their slide_number for quick lookup
        analyzed_slides_map = {}
        for slide_info in analysis.get('slides', []):
            analyzed_slides_map[slide_info['slide_number']] = slide_info

        slides_data = []
        slides_needing_demos = []

        for slide_num in range(1, len(slide_paths) + 1):
            # Convert absolute path to relative path for frontend access
            absolute_path = slide_paths[slide_num - 1]
            # Remove the leading /app/backend/ to get relative path
            relative_path = absolute_path
            if absolute_path.startswith('/app/backend/'):
                relative_path = absolute_path.replace('/app/backend/', '', 1)
            elif absolute_path.startswith('uploads/'):
                relative_path = absolute_path
            else:
                # Extract uploads/ path from absolute path
                parts = Path(absolute_path).parts
                if 'uploads' in parts:
                    uploads_idx = parts.index('uploads')
                    relative_path = str(Path(*parts[uploads_idx:]))

            # Check if this slide was analyzed
            slide_info = analyzed_slides_map.get(slide_num)
            needs_demo = slide_info.get('needs_demo', False) if slide_info else False

            slide_data = {
                "slide_number": slide_num,
                "image_path": relative_path,
                "title": slide_info.get('title', f'Slide {slide_num}') if slide_info else f'Slide {slide_num}',
                "description": slide_info.get('description', '') if slide_info else '',
                "needs_demo": needs_demo
            }

            if needs_demo and slide_info:
                slide_data['demo_reason'] = slide_info.get('reason', '')
                slide_data['demo_type'] = slide_info.get('demo_type', 'visualization')
                slides_needing_demos.append(slide_info)

            slides_data.append(slide_data)

        # Update document with slide data
        document.slide_count = len(slide_paths)
        document.slides_data = {"slides": slides_data}
        document.analysis_results = analysis

        # Template workflow: Search for templates and await user selection
        if use_templates and slides_needing_demos:
            logger.info(f"Template workflow: searching for {len(slides_needing_demos)} slides")
            template_options = await processor.demo_analyzer.search_templates_for_slides(
                slides_needing_demos=slides_needing_demos,
                user_preferences=user_prefs,
                max_results_per_slide=processing_config.get('max_template_results', 3)
            )

            # Store template options for user selection
            document.template_options = template_options
            document.status = "awaiting_template_selection"
            logger.info(f"Document {document_id} awaiting template selection: {len(template_options)} slides with templates")

            db.commit()
            db.refresh(document)

            total_time = time.time() - start_time
            logger.info(f"PPT analysis completed for document {document_id} in {total_time:.2f}s")

        # Non-template workflow: Generate demos directly with AI
        else:
            if not use_templates:
                logger.info(f"Template workflow disabled, using AI-only generation")
            else:
                logger.info(f"No slides need demos, completing processing")

            for slide_num in range(1, len(slide_paths) + 1):
                slide_data = slides_data[slide_num - 1]
                if slide_data.get('needs_demo'):
                    slide_info = analyzed_slides_map.get(slide_num)
                    logger.info(f"Generating demo for slide {slide_num}...")
                    demo_html = await processor.demo_analyzer.generate_demo_html(
                        slide_paths[slide_num - 1],
                        slide_info,
                        user_prefs
                    )
                    slide_data['demo_html'] = demo_html

            # Update document with generated demos
            document.slides_data = {"slides": slides_data}
            document.status = "ready"

            db.commit()
            db.refresh(document)

            total_time = time.time() - start_time
            logger.info(f"PPT processing completed for document {document_id} in {total_time:.2f}s")

    except Exception as e:
        logger.error(f"Error processing PPT document {document_id}: {e}")
        # Update document with error
        try:
            document = db.query(PPTDocument).filter(PPTDocument.id == document_id).first()
            if document:
                document.status = "error"
                document.error_message = str(e)
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update error status: {db_error}")

    finally:
        db.close()
