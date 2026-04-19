import os
import base64
import json
import io
import time
import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image
import PyPDF2
from abc import ABC, abstractmethod
from .prompts import ai_prompts
from dataclasses import dataclass, field
import re

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Data Model Classes for Modular Pipeline
# ============================================================================

@dataclass
class ScientificModel:
    """Stage 1 output"""
    core_formulas: List[str] = field(default_factory=list)           # core formulas
    principles: List[str] = field(default_factory=list)              # fundamental principles
    mechanism: List[str] = field(default_factory=list)               # working mechanism
    constraints: List[str] = field(default_factory=list)             # constraints to follow
    forbidden_errors: List[str] = field(default_factory=list)        # forbidden errors
    variable_relationships: Dict[str, str] = field(default_factory=dict)  # variable relationships
    validation_checks: List[str] = field(default_factory=list)       # validation checkpoints
    raw_analysis: str = ""                                           # raw analysis text

    @classmethod
    def from_dict(cls, data: Dict) -> 'ScientificModel':
        """Create ScientificModel from dictionary."""
        return cls(
            core_formulas=data.get('core_formulas', []),
            principles=data.get('principles', []),
            mechanism=data.get('mechanism', []),
            constraints=data.get('constraints', []),
            forbidden_errors=data.get('forbidden_errors', []),
            variable_relationships=data.get('variable_relationships', {}),
            validation_checks=data.get('validation_checks', []),
            raw_analysis=data.get('raw_analysis', '')
        )
    
# pdf2image removed - using PyMuPDF only

# Import PyMuPDF as a better alternative
try:
    import fitz  # PyMuPDF is imported as fitz
    PYMUPDF_AVAILABLE = True
    print("PyMuPDF (fitz) imported successfully")
except ImportError as e:
    PYMUPDF_AVAILABLE = False
    print(f"Warning: PyMuPDF not available. Error: {e}. Using fallback PDF processing method.")

# Import AI providers

try:
    from zai import ZhipuAiClient
    ZHIPU_AVAILABLE = True
except ImportError:
    ZHIPU_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic SDK not available. Install with: pip install anthropic")


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def analyze_content(self, images: List[Dict], user_preferences: Dict) -> Dict:
        """Analyze PDF content and return structured analysis."""
        pass

    @abstractmethod
    async def generate_website(self, images: List[Dict], analysis: Dict, user_preferences: Dict) -> Dict:
        """Generate interactive learning website."""
        pass

    @abstractmethod
    async def generate_website_from_concept(self, concept_data: Dict, user_preferences: Dict) -> Dict:
        """Generate interactive learning website from concept data."""
        pass

    @abstractmethod
    async def modify_website_ui(self, original_html: str, user_prompt: str, document_context: Dict) -> Dict:
        """Modify existing website UI based on user prompt."""
        pass

    @abstractmethod
    async def customize_template(
        self,
        template,
        content_info: Dict,
        user_preferences: Dict,
        customization_params: Optional[Dict] = None
    ) -> str:
        """Customize a template HTML using LLM."""
        pass

    @abstractmethod
    async def generate_knowledge_cards(self, analysis: Dict, user_preferences: Dict) -> Dict:
        """Generate prerequisite knowledge cards as markdown summaries."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of the AI provider."""
        pass


class EnglishProvider(AIProvider):
    """Unified English AI provider implementation using Chinese middle-transfer API for both Gemini and OpenAI models."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4.1"):
        """
        Initialize unified English provider.

        Args:
            api_key: API key for the middle-transfer service
            model: Model to use - supports both gemini-3-pro-image-preview and gpt-4.1
        """
        if not api_key:
            # Try multiple environment variables for flexibility
            api_key = (os.getenv("ENGLISH_API_KEY") or
                      os.getenv("MIDDLE_TRANSFER_API_KEY") or
                      os.getenv("GEMINI_API_KEY") or
                      os.getenv("OPENAI_API_KEY"))

        if not api_key:
            raise ValueError("API key not provided. Set ENGLISH_API_KEY, MIDDLE_TRANSFER_API_KEY, GEMINI_API_KEY, or OPENAI_API_KEY environment variable or pass api_key parameter.")

        self.api_key = api_key
        self.model = model
        self.base_url = "https://chatapi.onechats.ai/v1beta"

        # Validate model choice
        supported_models = [
            "gemini-3-pro-image-preview",
            "gpt-4.1",
            "gemini-pro-vision",
            "gpt-4-vision-preview"
        ]

        if self.model not in supported_models:
            print(f"Warning: Model '{self.model}' not in supported list {supported_models}. Using default 'gpt-4.1'")
            self.model = "gpt-4.1"

    async def analyze_content(self, images: List[Dict], user_preferences: Dict) -> Dict:
        """Analyze content using unified English API (supports both Gemini and OpenAI models)."""
        analysis_start = time.time()
        logger.info(f"🧠 Starting content analysis with {self.get_provider_name()} using {len(images)} images")

        user_preferences = user_preferences or {}
        grade_level = user_preferences.get('grade_level', 'middle school')
        interests = user_preferences.get('interests', [])

        # Prepare content for API
        prep_start = time.time()
        content = []

        # Add the text prompt
        prompt = self._get_content_analysis_prompt(grade_level, interests)
        content.append({"type": "text", "text": prompt})

        # Add images (limit to first 10 for token management)
        max_images = min(len(images), 10)
        for i in range(max_images):
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{images[i]['image_data']}",
                    "detail": "low"
                }
            })
        prep_time = time.time() - prep_start
        logger.info(f"📝 Content prepared for API in {prep_time:.2f}s - Using {max_images} images")

        try:
            api_start = time.time()
            response = await self._make_api_call(content)
            api_time = time.time() - api_start
            logger.info(f"🌐 AI API call completed in {api_time:.2f}s")

            parse_start = time.time()
            result = self._extract_json_from_response(response)
            parse_time = time.time() - parse_start
            logger.info(f"📄 Response parsed in {parse_time:.2f}s")

            total_analysis_time = time.time() - analysis_start
            logger.info(f"✅ Content analysis completed in {total_analysis_time:.2f}s total")
            return result
        except Exception as e:
            logger.error(f"❌ Error analyzing content with English Provider ({self.model}): {e}")
            return self._generate_fallback_analysis()

    async def generate_website(self, images: List[Dict], analysis: Dict, user_preferences: Dict) -> Dict:
        """Generate website using unified English API."""
        website_start = time.time()
        logger.info(f"🎨 Starting website generation with {self.get_provider_name()} using {len(images)} images")

        user_preferences = user_preferences or {}
        grade_level = user_preferences.get('grade_level', 6)
        interests = user_preferences.get('interests', [])

        # Prepare content for API
        prep_start = time.time()
        content = []

        # Add the website generation prompt
        prompt = self._get_website_generation_prompt(grade_level, interests, analysis)
        content.append({"type": "text", "text": prompt})

        # Add images for website generation (limit to 15 pages)
        max_images = min(len(images), 15)
        for i in range(max_images):
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{images[i]['image_data']}",
                    "detail": "low"
                }
            })
        prep_time = time.time() - prep_start
        logger.info(f"📝 Website content prepared in {prep_time:.2f}s - Using {max_images} images")

        try:
            api_start = time.time()
            response = await self._make_api_call(content)
            api_time = time.time() - api_start
            logger.info(f"🌐 Website API call completed in {api_time:.2f}s")

            parse_start = time.time()
            result = self._extract_json_from_response(response)
            parse_time = time.time() - parse_start
            logger.info(f"📄 Website response parsed in {parse_time:.2f}s")

            total_website_time = time.time() - website_start
            logger.info(f"✅ Website generation completed in {total_website_time:.2f}s total")
            return result
        except Exception as e:
            logger.error(f"❌ Error generating website with English Provider ({self.model}): {e}")
            return self._generate_fallback_website(images, analysis, user_preferences)

    def get_provider_name(self) -> str:
        """Get provider name with model info."""
        if "gemini" in self.model.lower():
            return f"Gemini ({self.model})"
        else:
            return f"OpenAI ({self.model})"

    async def generate_website_from_concept(self, concept_data: Dict, user_preferences: Dict) -> Dict:
        """Generate website from concept - not implemented for English provider."""
        raise NotImplementedError("generate_website_from_concept is not implemented for English provider. Please use Zhipu provider.")

    async def modify_website_ui(self, original_html: str, user_prompt: str, document_context: Dict) -> Dict:
        """Modify website UI - not implemented for English provider."""
        raise NotImplementedError("modify_website_ui is not implemented for English provider. Please use Zhipu provider.")

    async def generate_knowledge_cards(self, analysis: Dict, user_preferences: Dict) -> Dict:
        """Generate prerequisite knowledge cards - not implemented for English provider."""
        raise NotImplementedError("generate_knowledge_cards is not implemented for English provider. Please use Zhipu provider.")

    async def customize_template(
        self,
        template,
        content_info: Dict,
        user_preferences: Dict,
        customization_params: Optional[Dict] = None
    ) -> str:
        """Customize template - not implemented for English provider."""
        raise NotImplementedError("customize_template is not implemented for English provider. Please use Zhipu provider.")

    async def _make_api_call(self, content: List[Dict]) -> str:
        """Make API call to the middle-transfer service."""
        import httpx

        # Determine API endpoint based on model
        if "gemini" in self.model.lower():
            # Gemini-style endpoint
            endpoint = f"{self.base_url}/models/{self.model}:streamGenerateContent"
            payload = {
                "contents": [{
                    "role": "user",
                    "parts": content
                }],
                "generationConfig": {
                    "responseModalities": ["TEXT"],
                    "temperature": 0.7
                }
            }
        else:
            # OpenAI-style endpoint (default)
            endpoint = f"{self.base_url}/chat/completions"
            payload = {
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": content
                }],
                "max_tokens": 4000,
                "temperature": 0.7
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=900.0) as client:  # 15 minutes for long AI processing
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()

            if "gemini" in self.model.lower():
                # Gemini response format
                result = response.json()
                if 'candidates' in result and result['candidates']:
                    return result['candidates'][0]['content']['parts'][0]['text']
                else:
                    raise ValueError("Invalid Gemini response format")
            else:
                # OpenAI response format
                result = response.json()
                if 'choices' in result and result['choices']:
                    return result['choices'][0]['message']['content']
                else:
                    raise ValueError("Invalid OpenAI response format")

    def _extract_json_from_response(self, response_text: str) -> Dict:
        """Extract JSON from API response text."""
        if not response_text:
            return self._generate_fallback_analysis()

        # Try to extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                print(f"Failed to parse JSON from response, using fallback")
                return self._generate_fallback_analysis()

        # If no JSON found, return fallback
        return self._generate_fallback_analysis()

    def _get_content_analysis_prompt(self, grade_level: str, interests: List[str]) -> str:
        """Get the content analysis prompt for English providers."""
        return ai_prompts.english_content_analysis_prompt(grade_level, interests)

    def _get_knowledge_card_generation_prompt(self, analysis: Dict, user_preferences: Dict) -> str:
        """Get the knowledge card generation prompt for English providers."""
        return ai_prompts.english_knowledge_card_prompt(analysis)

    def _get_website_generation_prompt(self, grade_level: int, interests: List[str], analysis: Dict) -> str:
        """Get the website generation prompt for English providers."""
        return ai_prompts.english_website_generation_prompt(grade_level, interests, analysis)

    def _generate_fallback_analysis(self) -> Dict:
        """Generate fallback analysis when API fails."""
        return {
            "main_topics": ["Educational Content"],
            "key_concepts": ["Learning", "Understanding"],
            "learning_objectives": ["Comprehend the material"],
            "prerequisite_knowledge": [],
            "difficulty_level": "intermediate",
            "target_grade_level": 6,
            "content_structure": [],
            "visual_elements": [],
            "subject_area": "General Education"
        }

    def _generate_fallback_website(self, pdf_images: List[Dict], analysis: Dict, user_preferences: Optional[Dict] = None) -> Dict:
        """Generate fallback website."""
        user_preferences = user_preferences or {}
        grade_level = user_preferences.get('grade_level', 6)

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Interactive Learning - {analysis.get('subject_area', 'Education')}</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
            <div class="container mx-auto px-4 py-8">
                <header class="mb-8 text-center">
                    <h1 class="text-4xl font-bold text-blue-600 mb-2">
                        Interactive Learning
                    </h1>
                    <p class="text-gray-600">
                        Subject: {analysis.get('subject_area', 'Education')} | Grade Level: {grade_level} | AI: {self.get_provider_name()}
                    </p>
                </header>

                <nav class="mb-8">
                    <div class="flex flex-wrap gap-2 justify-center">
                        {"".join([f'<button onclick="scrollToPage({i+1})" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">Page {i+1}</button>' for i in range(min(len(pdf_images), 10))])}
                    </div>
                </nav>

                <main class="space-y-8">
                    <section class="bg-white rounded-lg shadow-lg p-6">
                        <h2 class="text-2xl font-semibold mb-4">Key Concepts</h2>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {"".join([f'<div class="bg-blue-50 p-4 rounded-lg"><h3 class="font-semibold">{concept}</h3><p class="text-sm text-gray-600">Important concept to understand</p></div>' for concept in analysis.get('key_concepts', ['Learning'])])}
                        </div>
                    </section>

                    <section class="bg-white rounded-lg shadow-lg p-6">
                        <h2 class="text-2xl font-semibold mb-4">Content Pages</h2>
                        <div class="space-y-8">
                            {"".join([f'''
                            <div class="page-section" id="page-{page['page']}">
                                <h3 class="text-xl font-semibold mb-4">Page {page['page']}</h3>
                                <div class="bg-gray-50 rounded-lg p-4">
                                    <img src="data:image/jpeg;base64,{page['image_data']}"
                                         alt="Page {page['page']}"
                                         class="w-full max-w-4xl mx-auto shadow-md rounded">
                                </div>
                            </div>
                            ''' for page in pdf_images[:10]])}
                        </div>
                    </section>

                    <section class="bg-green-50 rounded-lg p-6">
                        <h3 class="text-xl font-semibold mb-3">Learning Objectives</h3>
                        <ul class="list-disc list-inside space-y-2">
                            {"".join([f'<li>{obj}</li>' for obj in analysis.get('learning_objectives', ['Understand the content'])])}
                        </ul>
                    </section>
                </main>
            </div>

            <script>
                function scrollToPage(pageNum) {{
                    const element = document.getElementById('page-' + pageNum);
                    if (element) {{
                        element.scrollIntoView({{ behavior: 'smooth' }});
                    }}
                }}
            </script>
        </body>
        </html>
        """

        return {
            "html": html_content,
            "metadata": {
                "title": f"Interactive Learning - {analysis.get('subject_area', 'Education')}",
                "subject": analysis.get('subject_area', 'Education'),
                "grade_level": grade_level,
                "estimated_time_minutes": 30,
                "learning_objectives": analysis.get('learning_objectives', ['Understand the content']),
                "ai_provider": self.get_provider_name()
            },
            "interactive_elements": []
        }


class ChineseProvider(AIProvider):
    """Unified Chinese AI provider supporting both Anthropic and Zhipu models."""

    # Model detection
    ANTHROPIC_MODELS = ["claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5-20251001"]
    ZHIPU_MODELS = ["glm-4.7", "glm-4.6", "glm-4.6v"]

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "glm-4.6v",
        base_url: Optional[str] = None
    ):
        """
        Initialize the Chinese Provider.

        Args:
            api_key: API key. If not provided, auto-detects from environment based on model.
            model: Model to use. Determines which backend (Anthropic vs Zhipu) to use.
            base_url: Optional base URL for Anthropic API (for proxy usage).
        """
        self.model = model
        self.backend = self._detect_backend(model)

        # Auto-detect API key based on backend
        if not api_key:
            if self.backend == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")
            else:
                api_key = os.getenv("ZHIPU_API_KEY")

        if not api_key:
            env_var = "ANTHROPIC_API_KEY" if self.backend == "anthropic" else "ZHIPU_API_KEY"
            raise ValueError(f"API key not provided. Set {env_var} environment variable or pass api_key parameter.")

        # Initialize appropriate client
        if self.backend == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("Anthropic SDK not installed. Install with: pip install anthropic")

            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            elif os.getenv("ANTHROPIC_BASE_URL"):
                client_kwargs["base_url"] = os.getenv("ANTHROPIC_BASE_URL")

            self.anthropic_client = Anthropic(**client_kwargs)
            self.zhipu_client = None
            self.text_model = model
            logger.info(f"🎨 ChineseProvider initialized with Anthropic backend, model: {self.model}")
        else:  # zhipu
            if not ZHIPU_AVAILABLE:
                raise ImportError("Zhipu AI SDK not installed. Install with: pip install zai-sdk")

            self.zhipu_client = ZhipuAiClient(api_key=api_key)
            self.anthropic_client = None
            self.default_text_model = os.getenv("ZHIPU_TEXT_MODEL", "glm-4.6")
            self.text_model = self.default_text_model
            logger.info(f"🎨 ChineseProvider initialized with Zhipu backend, model: {self.model}")

    def _detect_backend(self, model: str) -> str:
        """Detect which backend to use based on model name."""
        if model.startswith("claude-") or model in self.ANTHROPIC_MODELS:
            return "anthropic"
        return "zhipu"  # Default to Zhipu for Chinese provider

    def _map_grade_level_to_string(self, grade_level: int) -> str:
        """Convert integer grade level to Chinese grade level string."""
        grade_mapping = {
            0: "幼儿园",
            1: "小学一年级",
            2: "小学二年级",
            3: "小学三年级",
            4: "小学四年级",
            5: "小学五年级",
            6: "小学六年级",
            7: "初中一年级",
            8: "初中二年级",
            9: "初中三年级",
            10: "高中一年级",
            11: "高中二年级",
            12: "高中三年级",
            13: "本科",
            14: "研究生"
        }
        return grade_mapping.get(grade_level, f"年级{grade_level}")

    async def _run_zhipu_call(self, model: str, messages: List[Dict], thinking_params: Optional[Dict] = None, max_tokens: Optional[int] = None) -> Any:
        """Run synchronous Zhipu API call in a thread pool to avoid blocking the event loop.

        Args:
            model: Model name to use
            messages: List of message dicts
            thinking_params: Optional thinking parameters
            max_tokens: Optional max tokens limit for response
        """
        if self.zhipu_client is None:
            raise RuntimeError("Zhipu client not initialized. This provider is configured for Anthropic.")

        def _make_sync_call():
            params = {
                "model": model,
                "messages": messages,
            }
            if thinking_params:
                params["thinking"] = thinking_params
            if max_tokens:
                params["max_tokens"] = max_tokens

            return self.zhipu_client.chat.completions.create(**params)

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _make_sync_call)

        # Log truncation reason for diagnostics.
        try:
            finish_reason = None
            if response and getattr(response, "choices", None):
                first_choice = response.choices[0]
                finish_reason = getattr(first_choice, "finish_reason", None)

            if finish_reason in ["length", "max_tokens"]:
                logger.warning(
                    "⚠️ Zhipu response may be truncated: finish_reason=%s, model=%s, max_tokens=%s",
                    finish_reason,
                    model,
                    max_tokens
                )
        except Exception:
            # Never break generation due to diagnostic logging.
            pass

        return response

    # Threshold for using streaming (to avoid 10-minute timeout for large responses)
    ANTHROPIC_STREAMING_THRESHOLD = 16000

    async def _run_anthropic_call(
        self,
        model: str,
        messages: List[Dict],
        max_tokens: int = 64000,
        thinking_enabled: bool = False
    ) -> Any:
        """Run synchronous Anthropic API call in a thread pool to avoid blocking the event loop.

        Uses streaming for large max_tokens to avoid 10-minute timeout errors.
        """
        if self.anthropic_client is None:
            raise RuntimeError("Anthropic client not initialized. This provider is configured for Zhipu.")

        use_streaming = max_tokens > self.ANTHROPIC_STREAMING_THRESHOLD

        def _make_sync_call():
            params = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": messages
            }
            # Extended thinking support for compatible models
            if thinking_enabled and "claude-3-7" in model:
                params["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": 4096
                }

            if use_streaming:
                # Use streaming for large responses to avoid 10-minute timeout
                logger.info(f"🔄 Using streaming mode for Anthropic API call (max_tokens={max_tokens})")
                return self._collect_streaming_response(params)
            else:
                return self.anthropic_client.messages.create(**params)

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _make_sync_call)

        # Log truncation reason for diagnostics.
        try:
            stop_reason = getattr(response, "stop_reason", None) if response else None
            if stop_reason in ["max_tokens", "model_context_window_exceeded"]:
                logger.warning(
                    "⚠️ Anthropic response may be truncated: stop_reason=%s, model=%s, max_tokens=%s",
                    stop_reason,
                    model,
                    max_tokens
                )
        except Exception:
            # Never break generation due to diagnostic logging.
            pass

        return response

    def _collect_streaming_response(self, params: Dict) -> Any:
        """Collect streaming response from Anthropic API and return a response-like object."""
        from dataclasses import dataclass, field
        from typing import List as TypingList

        @dataclass
        class TextBlock:
            text: str
            type: str = "text"

        @dataclass
        class StreamedResponse:
            content: TypingList[TextBlock] = field(default_factory=list)
            stop_reason: str = ""
            model: str = ""
            usage: Dict = field(default_factory=dict)

        collected_text = []
        stop_reason = ""
        model_used = params.get("model", "")
        usage_info = {}

        with self.anthropic_client.messages.stream(**params) as stream:
            for text in stream.text_stream:
                collected_text.append(text)

            # Get final message info after streaming completes
            final_message = stream.get_final_message()
            if final_message:
                stop_reason = getattr(final_message, "stop_reason", "")
                model_used = getattr(final_message, "model", model_used)
                usage_info = getattr(final_message, "usage", {})
                if hasattr(usage_info, "__dict__"):
                    usage_info = usage_info.__dict__

        full_text = "".join(collected_text)
        logger.info(f"✅ Streaming completed, collected {len(full_text)} characters")

        return StreamedResponse(
            content=[TextBlock(text=full_text)],
            stop_reason=stop_reason,
            model=model_used,
            usage=usage_info
        )

    def _extract_text_from_anthropic_response(self, response) -> str:
        """Extract text content from Anthropic response."""
        if response and response.content:
            content_text = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    content_text += block.text
            return content_text
        return ""

    async def analyze_content(self, images: List[Dict], user_preferences: Dict) -> Dict:
        """Analyze content using the appropriate backend."""
        analysis_start = time.time()
        logger.info(f"🧠 Starting content analysis with ChineseProvider ({self.backend}) using {len(images)} images")

        user_preferences = user_preferences or {}
        grade_level_int = user_preferences.get('grade_level', 6)
        grade_level = self._map_grade_level_to_string(grade_level_int)
        interests = user_preferences.get('interests', [])

        # Prepare images (limit to first 5 pages due to context limits)
        max_pages = min(len(images), 5)

        if self.backend == "anthropic":
            return await self._analyze_content_anthropic(images, max_pages, grade_level, interests, analysis_start)
        else:
            return await self._analyze_content_zhipu(images, max_pages, grade_level, interests, analysis_start)

    async def _analyze_content_anthropic(self, images: List[Dict], max_pages: int, grade_level: str, interests: List[str], analysis_start: float) -> Dict:
        """Analyze content using Anthropic."""
        content = []
        prompt = self._get_content_analysis_prompt(grade_level, interests)

        # Add images
        for i in range(max_pages):
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": images[i]['image_data']
                }
            })

        content.append({"type": "text", "text": prompt})

        try:
            api_start = time.time()
            response = await self._run_anthropic_call(
                model=self.model,
                messages=[{"role": "user", "content": content}],
                max_tokens=4096
            )
            api_time = time.time() - api_start
            logger.info(f"🌐 Anthropic API call completed in {api_time:.2f}s")

            content_text = self._extract_text_from_anthropic_response(response)
            if content_text:
                json_start = content_text.find('{')
                json_end = content_text.rfind('}') + 1

                if json_start != -1 and json_end > json_start:
                    json_str = content_text[json_start:json_end]
                    result = json.loads(json_str)
                    total_analysis_time = time.time() - analysis_start
                    logger.info(f"✅ Anthropic content analysis completed in {total_analysis_time:.2f}s total")
                    return result

            logger.warning(f"⚠️ Using fallback analysis for Anthropic")
            return self._generate_fallback_analysis()

        except Exception as e:
            logger.error(f"❌ Error analyzing content with Anthropic: {e}")
            return self._generate_fallback_analysis()

    async def _analyze_content_zhipu(self, images: List[Dict], max_pages: int, grade_level: str, interests: List[str], analysis_start: float) -> Dict:
        """Analyze content using Zhipu."""
        content = []
        prompt = self._get_content_analysis_prompt(grade_level, interests)
        content.append({"type": "text", "text": prompt})

        # Add images
        for i in range(max_pages):
            content.append({
                "type": "image_url",
                "image_url": {"url": images[i]['image_data']}
            })

        try:
            api_start = time.time()
            response = await self._run_zhipu_call(
                model=self.model,
                messages=[{"role": "user", "content": content}],
                thinking_params={"type": "disabled"}
            )
            api_time = time.time() - api_start
            logger.info(f"🌐 Zhipu API call completed in {api_time:.2f}s")

            if response and response.choices and response.choices[0].message:
                content_text = response.choices[0].message.content
                content_text = content_text.replace("```html", "")

                if content_text:
                    json_start = content_text.find('{')
                    json_end = content_text.rfind('}') + 1

                    if json_start != -1 and json_end > json_start:
                        json_str = content_text[json_start:json_end]
                        result = json.loads(json_str)
                        total_analysis_time = time.time() - analysis_start
                        logger.info(f"✅ Zhipu content analysis completed in {total_analysis_time:.2f}s total")
                        return result

            logger.warning(f"⚠️ Using fallback analysis for Zhipu")
            return self._generate_fallback_analysis()

        except Exception as e:
            logger.error(f"❌ Error analyzing content with Zhipu: {e}")
            return self._generate_fallback_analysis()

    async def generate_website(self, pdf_images: List[Dict], analysis: Dict, user_preferences: Dict) -> Dict:
        """Generate interactive learning website using the appropriate backend."""
        website_start = time.time()
        logger.info(f"🎨 Starting website generation with ChineseProvider ({self.backend})")

        user_preferences = user_preferences or {}

        try:
            # Extract procedural concepts from analysis
            procedural_concepts = analysis.get('procedural_concepts', [])
            if not procedural_concepts:
                procedural_concepts = [
                    {
                        "name": concept,
                        "description": f"Understanding and applying the concept of {concept}",
                        "key_steps": ["Step 1: Understand the concept", "Step 2: Practice with examples", "Step 3: Apply to problems"],
                        "complexity": "中等"
                    }
                    for concept in analysis.get('key_concepts', [])[:2]
                ]

            procedural_concepts = procedural_concepts[:3]

            # Generate HTML content
            html_content = await self._generate_html_content(procedural_concepts, analysis, user_preferences)

            # Generate metadata and interactive elements
            metadata_and_elements = await self._generate_metadata_and_interactive(procedural_concepts, analysis, user_preferences)

            total_website_time = time.time() - website_start
            logger.info(f"✅ Website generation completed in {total_website_time:.2f}s total")

            return {
                "html": html_content,
                "metadata": metadata_and_elements.get("metadata", {}),
                "interactive_elements": metadata_and_elements.get("interactive_elements", [])
            }

        except Exception as e:
            logger.error(f"❌ Error generating website: {e}")
            return self._generate_fallback_website(pdf_images, analysis, user_preferences)

    async def generate_website_from_concept(self, concept_data: Dict, user_preferences: Dict) -> Dict:
        """Generate interactive learning website from concept data."""
        try:
            pipeline_start = time.time()
            logger.info(f"🎨 Starting concept-based website generation with ChineseProvider ({self.backend})")

            if self.backend == "anthropic":
                return await self._generate_website_from_concept_anthropic(concept_data, user_preferences, pipeline_start)
            else:
                # Use modular pipeline for Zhipu
                pipeline = ModularGenerationPipeline(self)
                result = await pipeline.execute(concept_data, user_preferences)
                return result

        except Exception as e:
            logger.error(f"❌ Pipeline failed: {str(e)}")
            raise

    async def _generate_website_from_concept_anthropic(self, concept_data: Dict, user_preferences: Dict, pipeline_start: float) -> Dict:
        """Generate website from concept using Anthropic."""
        grade_level_int = user_preferences.get('grade_level', 10)
        grade_level = self._map_grade_level_to_string(grade_level_int)

        # Stage 1: Scientific modeling
        logger.info("[1/3] Scientific modeling stage...")
        scientific_prompt = ai_prompts.anthropic_scientific_prompt(concept_data)

        sci_response = await self._run_anthropic_call(
            model=self.model,
            messages=[{"role": "user", "content": scientific_prompt}],
            max_tokens=4096
        )

        sci_text = self._extract_text_from_anthropic_response(sci_response)
        scientific_analysis = sci_text

        # Parse scientific model
        constraints_summary = ""
        try:
            json_start = sci_text.find('{')
            json_end = sci_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                sci_data = json.loads(sci_text[json_start:json_end])
                if sci_data.get('core_formulas'):
                    constraints_summary += f"核心公式: {', '.join(sci_data['core_formulas'][:3])}\n"
                if sci_data.get('mechanism'):
                    constraints_summary += f"工作原理: {'; '.join(sci_data['mechanism'][:3])}\n"
                if sci_data.get('constraints'):
                    constraints_summary += f"必须遵守: {'; '.join(sci_data['constraints'][:2])}"
        except:
            constraints_summary = "科学准确性优先"

        # Stage 2: Generate interactive website
        logger.info("[2/3] Generating interactive website...")
        html_prompt = ai_prompts.anthropic_concept_html_prompt(
            concept_data,
            constraints_summary
        )

        html_response = await self._run_anthropic_call(
            model=self.model,
            messages=[{"role": "user", "content": html_prompt}],
            max_tokens=64000
        )

        html_text = self._extract_text_from_anthropic_response(html_response)
        html_text = html_text.replace("```html", "").replace("```HTML", "").replace("```", "").strip()

        # Extract HTML from response
        html_start = html_text.find('<!DOCTYPE html>')
        if html_start == -1:
            html_start = html_text.find('<html')
        html_end_index = html_text.rfind('</html>')
        html_end = html_end_index + len('</html>') if html_end_index != -1 else -1

        if html_start != -1 and html_end > html_start:
            final_html = html_text[html_start:html_end]
        elif html_start != -1:
            final_html = html_text[html_start:]
        else:
            final_html = html_text

        # Stage 3: Post-processing (inject KaTeX)
        logger.info("[3/3] Injecting formula rendering engine...")
        final_html = self._inject_katex(final_html)

        total_time = time.time() - pipeline_start
        logger.info(f"✅ Generation completed! Total time: {total_time:.1f}s")

        return {
            "html": final_html,
            "scientific_analysis": scientific_analysis,
            "metadata": {
                "title": f"交互式学习 - {concept_data.get('concept_name', '')}",
                "total_time_seconds": round(total_time, 2),
                "ai_provider": f"ChineseProvider-Anthropic-{self.model}"
            }
        }

    def _inject_katex(self, html: str) -> str:
        """Inject KaTeX resources for math rendering."""
        katex_injection = """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
<script>
document.addEventListener("DOMContentLoaded", function() {
    renderMathInElement(document.body, {
        delimiters: [
            {left: '\\\\[', right: '\\\\]', display: true},
            {left: '\\\\(', right: '\\\\)', display: false},
            {left: '$$', right: '$$', display: true},
            {left: '$', right: '$', display: false}
        ],
        throwOnError: false
    });
});
</script>"""
        if '</head>' in html:
            return html.replace('</head>', katex_injection + '</head>')
        return html + katex_injection

    async def modify_website_ui(self, original_html: str, user_prompt: str, document_context: Dict) -> Dict:
        """Modify website UI using the appropriate backend."""
        modification_start = time.time()
        logger.info(f"🎨 Starting UI modification with ChineseProvider ({self.backend})")

        try:
            if self.backend == "anthropic":
                prompt = ai_prompts.anthropic_modify_ui_prompt(original_html, user_prompt, document_context)
                response = await self._run_anthropic_call(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=64000
                )
                content_text = self._extract_text_from_anthropic_response(response)
            else:
                prompt = ai_prompts.zhipu_modify_ui_prompt(original_html, user_prompt, document_context)
                response = await self._run_zhipu_call(
                    model=self.text_model,
                    messages=[{"role": "user", "content": prompt}],
                    thinking_params={"type": "enabled"}
                )
                content_text = response.choices[0].message.content if response and response.choices else ""

            if content_text:
                content_text = content_text.replace("```html", "").replace("```HTML", "").replace("```", "").strip()
                html_start = content_text.find('<!DOCTYPE html>')
                if html_start == -1:
                    html_start = content_text.find('<html')
                html_end_index = content_text.rfind('</html>')
                html_end = html_end_index + len('</html>') if html_end_index != -1 else -1

                if html_start != -1 and html_end > html_start:
                    modified_html = content_text[html_start:html_end]
                elif html_start != -1:
                    modified_html = content_text[html_start:]
                else:
                    modified_html = content_text

                total_time = time.time() - modification_start
                logger.info(f"✅ UI modification completed in {total_time:.2f}s")

                return {
                    "status": "success",
                    "modified_html": modified_html
                }

            return {
                "status": "success",
                "modified_html": original_html
            }

        except Exception as e:
            logger.error(f"❌ Error modifying UI: {e}")
            return {
                "status": "error",
                "error": str(e),
                "modified_html": original_html
            }

    async def generate_knowledge_cards(self, analysis: Dict, user_preferences: Dict) -> Dict:
        """Generate prerequisite knowledge cards."""
        logger.info(f"🖼️ Starting knowledge card generation with ChineseProvider ({self.backend})")

        prompt = self._get_knowledge_card_generation_prompt(analysis, user_preferences)

        try:
            if self.backend == "anthropic":
                response = await self._run_anthropic_call(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4096
                )
                content_text = self._extract_text_from_anthropic_response(response)
            else:
                response = await self._run_zhipu_call(
                    model=self.text_model,
                    messages=[{"role": "user", "content": prompt}],
                    thinking_params={"type": "disabled"}
                )
                content_text = response.choices[0].message.content if response and response.choices else ""

            if content_text:
                json_start = content_text.find('{')
                json_end = content_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    result = json.loads(content_text[json_start:json_end])
                    if isinstance(result, dict) and "cards" in result:
                        return result

            return {"cards": []}

        except Exception as e:
            logger.error(f"Error generating knowledge cards: {e}")
            return {"cards": []}

    async def customize_template(
        self,
        template,
        content_info: Dict,
        user_preferences: Dict,
        customization_params: Optional[Dict] = None
    ) -> str:
        """Customize a template HTML using LLM."""
        from .template_customizer import TemplateCustomizer
        customizer = TemplateCustomizer(self)
        return await customizer.customize_template(
            template=template,
            content_info=content_info,
            user_preferences=user_preferences,
            customization_params=customization_params
        )

    def get_provider_name(self) -> str:
        """Get the name of the AI provider."""
        if self.backend == "anthropic":
            return f"ChineseProvider-Anthropic ({self.model})"
        return f"ChineseProvider-Zhipu ({self.model})"

    async def _generate_html_content(self, procedural_concepts: List[Dict], analysis: Dict, user_preferences: Dict) -> str:
        """Generate HTML content only."""
        grade_level_int = user_preferences.get('grade_level', 6)
        grade_level = self._map_grade_level_to_string(grade_level_int)
        interests = user_preferences.get('interests', [])
        user_instruction = user_preferences.get('description', '无')

        try:
            if self.backend == "anthropic":
                prompt = ai_prompts.anthropic_procedural_html_prompt(
                    procedural_concepts, grade_level, interests, user_instruction
                )
                response = await self._run_anthropic_call(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=64000
                )
                content_text = self._extract_text_from_anthropic_response(response)
            else:
                prompt = ai_prompts.zhipu_one_shot_html_prompt(
                    procedural_concepts, grade_level, interests, user_instruction
                )
                response = await self._run_zhipu_call(
                    model=self.text_model,
                    messages=[{"role": "user", "content": prompt}],
                    thinking_params={"type": "enabled"}
                )
                content_text = response.choices[0].message.content if response and response.choices else ""

            if content_text:
                content_text = content_text.replace("```html", "").replace("```HTML", "").replace("```", "").strip()
                html_start = content_text.find('<!DOCTYPE html>')
                if html_start == -1:
                    html_start = content_text.find('<html')
                html_end_index = content_text.rfind('</html>')
                html_end = html_end_index + len('</html>') if html_end_index != -1 else -1

                if html_start != -1 and html_end > html_start:
                    return content_text[html_start:html_end]
                if html_start != -1:
                    return content_text[html_start:]
                return content_text

            return self._generate_fallback_html([], analysis, user_preferences)

        except Exception as e:
            logger.error(f"Error generating HTML content: {e}")
            return self._generate_fallback_html([], analysis, user_preferences)

    async def _generate_metadata_and_interactive(self, procedural_concepts: List[Dict], analysis: Dict, user_preferences: Dict) -> Dict:
        """Generate metadata and interactive elements only."""
        grade_level_int = user_preferences.get('grade_level', 6)
        grade_level = self._map_grade_level_to_string(grade_level_int)
        interests = user_preferences.get('interests', [])

        try:
            if self.backend == "anthropic":
                prompt = ai_prompts.anthropic_procedural_metadata_prompt(
                    procedural_concepts, analysis, grade_level
                )
                response = await self._run_anthropic_call(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4096
                )
                content_text = self._extract_text_from_anthropic_response(response)
            else:
                prompt = ai_prompts.zhipu_procedural_metadata_prompt(
                    procedural_concepts, analysis, grade_level, interests
                )
                response = await self._run_zhipu_call(
                    model=self.text_model,
                    messages=[{"role": "user", "content": prompt}],
                    thinking_params={"type": "disabled"}
                )
                content_text = response.choices[0].message.content if response and response.choices else ""

            if content_text:
                json_start = content_text.find('{')
                json_end = content_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = content_text[json_start:json_end]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass

            return self._generate_fallback_metadata([], analysis, user_preferences)

        except Exception as e:
            logger.error(f"Error generating metadata and interactive elements: {e}")
            return self._generate_fallback_metadata([], analysis, user_preferences)

    def _get_content_analysis_prompt(self, grade_level: str, interests: List[str]) -> str:
        """Get the content analysis prompt."""
        if self.backend == "anthropic":
            return ai_prompts.anthropic_content_analysis_prompt(grade_level, interests)
        return ai_prompts.zhipu_content_analysis_prompt(grade_level, interests)

    def _get_knowledge_card_generation_prompt(self, analysis: Dict, user_preferences: Dict) -> str:
        """Get the knowledge card generation prompt."""
        if self.backend == "anthropic":
            return ai_prompts.anthropic_knowledge_card_prompt(analysis)
        return ai_prompts.zhipu_knowledge_card_prompt(analysis)

    def _generate_fallback_analysis(self) -> Dict:
        """Generate fallback analysis when API fails."""
        return {
            "main_topics": ["教育内容"],
            "key_concepts": ["学习", "理解"],
            "learning_objectives": ["理解材料"],
            "prerequisite_knowledge": [],
            "difficulty_level": "中级",
            "target_grade_level": 6,
            "content_structure": [],
            "visual_elements": [],
            "subject_area": "综合教育",
            "procedural_concepts": [
                {
                    "name": "基本学习过程",
                    "description": "理解和掌握基本学习步骤",
                    "key_steps": ["理解概念", "练习应用", "检查掌握程度"],
                    "complexity": "简单"
                }
            ]
        }

    def _generate_fallback_html(self, pdf_images: List[Dict], analysis: Dict, user_preferences: Optional[Dict] = None) -> str:
        """Generate fallback HTML content."""
        user_preferences = user_preferences or {}
        grade_level = self._map_grade_level_to_string(user_preferences.get('grade_level', 6))
        subject = analysis.get('subject_area', '教育')

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>交互式学习 - {subject}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-purple-50 to-blue-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <header class="mb-8 text-center">
            <h1 class="text-4xl font-bold text-purple-600 mb-2">交互式学习平台</h1>
            <p class="text-gray-600">学科: {subject} | 年级: {grade_level} | AI: ChineseProvider</p>
        </header>
        <main class="bg-white rounded-lg shadow-lg p-6">
            <h2 class="text-2xl font-semibold mb-4">欢迎开始学习</h2>
            <p class="text-gray-600">内容正在生成中，请稍候...</p>
        </main>
    </div>
</body>
</html>"""

    def _generate_fallback_metadata(self, pdf_images: List[Dict], analysis: Dict, user_preferences: Optional[Dict] = None) -> Dict:
        """Generate fallback metadata."""
        user_preferences = user_preferences or {}
        grade_level = self._map_grade_level_to_string(user_preferences.get('grade_level', 6))
        subject = analysis.get('subject_area', '教育')

        return {
            "metadata": {
                "title": f"交互式{subject}学习",
                "subject": subject,
                "grade_level": grade_level,
                "estimated_time_minutes": 30,
                "learning_objectives": [f"理解{subject}的基本概念"],
                "ai_provider": self.get_provider_name()
            },
            "interactive_elements": []
        }

    def _generate_fallback_website(self, pdf_images: List[Dict], analysis: Dict, user_preferences: Optional[Dict] = None) -> Dict:
        """Generate fallback website."""
        return {
            "html": self._generate_fallback_html(pdf_images, analysis, user_preferences),
            "metadata": self._generate_fallback_metadata(pdf_images, analysis, user_preferences).get("metadata", {}),
            "interactive_elements": []
        }


# ============================================================================
# Modular Pipeline Classes for Scientific-First Generation
# ============================================================================

class ScientificEngine:
    """Stage 1: Scientific fact modeler - responsible for extracting core principles and constraints"""

    def __init__(self, ai_provider):
        self.ai_provider = ai_provider

    async def run(self, concept_data: Dict) -> 'ScientificModel':
        print(f"[1/3] Scientific modeling stage...")
        prompt = self._build_prompt(concept_data)
        
        try:
            response = await self.ai_provider._run_zhipu_call(
                model=self.ai_provider.text_model,
                messages=[{"role": "user", "content": prompt}],
                thinking_params={"type": "enabled"}
            )

            if response and response.choices and response.choices[0].message:
                content_text = response.choices[0].message.content
                
                # Logic preserved: precisely extract JSON portion
                json_start = content_text.find('{')
                json_end = content_text.rfind('}') + 1

                if json_start != -1 and json_end > json_start:
                    json_str = content_text[json_start:json_end]
                    data = json.loads(json_str)
                    model = ScientificModel.from_dict(data)
                    model.raw_analysis = content_text
                    return model

                return self._fallback_extraction(content_text)
        except Exception as e:
            print(f"Modeling failed: {e}")
            return ScientificModel(raw_analysis="Error during modeling")

    def _build_prompt(self, concept_data: Dict) -> str:
        """Build scientific modeling prompt using centralized prompt template."""
        return ai_prompts.anthropic_scientific_prompt(concept_data)

    def _fallback_extraction(self, text: str) -> 'ScientificModel':
        # Original logic preserved: extract from unstructured text
        model = ScientificModel(raw_analysis=text)
        formula_pattern = r'\$\$?([^$]+)\$\$?'
        model.core_formulas = re.findall(formula_pattern, text) or ["未识别到公式"]
        model.constraints = ["科学准确性优先"]
        model.forbidden_errors = ["不得违背基本物理定律"]
        return model


class VisualEngine:
    """Stage 2: Interactive visual builder - responsible for generating HTML/JS"""
    
    def __init__(self, ai_provider):
        self.ai_provider = ai_provider

    async def run(self, concept_data: Dict, scientific_model: 'ScientificModel', user_prefs: Dict) -> str:
        print(f"[2/3] Generating interactive website...")
        
        constraints_summary = self._format_constraints(scientific_model)
        grade_level = self.ai_provider._map_grade_level_to_string(user_prefs.get('grade_level', 10))
        
        prompt = ai_prompts.visual_engine_prompt(
                concept_data,
                constraints_summary,
                grade_level
        )
        print("Generated prompt for visual engine.")
        print("Prompt preview:", prompt[:5000], "...\n")
        print("Using ai provider model:", self.ai_provider.text_model)
        response = await self.ai_provider._run_zhipu_call(
            model=self.ai_provider.text_model,
            messages=[{"role": "user", "content": prompt}],
            thinking_params={"type": "enabled"},
            max_tokens=64000  # Increased for long HTML generation
        )
        
        if response and response.choices and response.choices[0].message:
            content_text = response.choices[0].message.content
            content_text = content_text.replace("```html", "").replace("```HTML", "").replace("```", "").strip()
            # Logic preserved: precisely extract content between HTML tags
            html_start = content_text.find('<!DOCTYPE html>')
            if html_start == -1: html_start = content_text.find('<html')
            html_end_index = content_text.rfind('</html>')
            html_end = html_end_index + len('</html>') if html_end_index != -1 else -1

            if html_start != -1 and html_end > html_start:
                return content_text[html_start:html_end]
            if html_start != -1:
                return content_text[html_start:]
            return content_text
        return ""

    def _format_constraints(self, model: 'ScientificModel') -> str:
        # Original logic preserved: original constraint formatting method
        lines = []
        if model.core_formulas: lines.append(f"核心公式: {', '.join(model.core_formulas[:3])}")
        if model.mechanism: lines.append(f"工作原理: {'; '.join(model.mechanism[:3])}")
        if model.constraints: lines.append(f"必须遵守: {'; '.join(model.constraints[:2])}")
        # if model.forbidden_errors: lines.append(f"严禁: {', '.join(model.forbidden_errors[:2])}")
        # if model.validation_checks: lines.append(f"验证检查: {'; '.join(model.validation_checks[:2])}")
        return '\n'.join(lines)


class PostProcessor:
    """Stage 3: Post-rendering processor - handles LaTeX and static resources"""
    
    @staticmethod
    def run(html_content: str) -> str:
        print(f"[3/3] Injecting formula rendering engine and cleaning...")

        # 1. Logic preserved: convert LaTeX delimiters and protect scripts
        processed_html = PostProcessor._convert_latex_delimiters(html_content)

        # 2. Logic preserved: inject KaTeX resources
        if 'katex' not in processed_html.lower():
            processed_html = PostProcessor._inject_katex(processed_html)

        return processed_html

    @staticmethod
    def _convert_latex_delimiters(html: str) -> str:
        # Original logic preserved: script tag protection logic
        script_blocks = []
        def protect_script(match):
            script_blocks.append(match.group(0))
            return f"__SCRIPT_BLOCK_{len(script_blocks)-1}__"

        html = re.sub(r'<script[^>]*>.*?</script>', protect_script, html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'\$\$([^$]+)\$\$', r'\\[\1\\]', html)
        html = re.sub(r'\$([^$\n]+?)\$', r'\\(\1\\)', html)

        for i, block in enumerate(script_blocks):
            html = html.replace(f"__SCRIPT_BLOCK_{i}__", block)
        return html

    @staticmethod
    def _inject_katex(html: str) -> str:
        katex_injection = """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
<script>
document.addEventListener("DOMContentLoaded", function() {
    const katexOptions = {
        delimiters: [
            {left: '\\\\[', right: '\\\\]', display: true},
            {left: '\\\\(', right: '\\\\)', display: false}, 
            {left: '$$', right: '$$', display: true}, 
            {left: '$', right: '$', display: false}
        ],
        throwOnError: false,
        strict: false,
        trust: true
    };

    // 1. define a safe render function with debounce
    let renderTimeout;
    function safeRender() {
        if (renderTimeout) clearTimeout(renderTimeout);
        renderTimeout = setTimeout(() => {
            renderMathInElement(document.body, katexOptions);
        }, 100);
    }

    // 2. Initial render
    renderMathInElement(document.body, katexOptions);

    // 3. Set up MutationObserver to watch for DOM changes
    const observer = new MutationObserver((mutations) => {
        let shouldRender = false;
        mutations.forEach((mutation) => {
            if (mutation.target && 
                mutation.target.className && 
                typeof mutation.target.className === 'string' && 
                mutation.target.className.includes('katex')) {
                return;
            }
            shouldRender = true;
        });
        
        if (shouldRender) {
            safeRender();
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true
    });
    
    // 4. Periodic check for any remaining unrendered LaTeX
    setInterval(() => {
        const text = document.body.innerText;
        if (text.includes('\\\\(') || text.includes('$$')) {
            safeRender();
        }
    }, 2000);
});
</script>"""
        return html.replace('</head>', katex_injection + '</head>') if '</head>' in html else html + katex_injection
    
class ModularGenerationPipeline:
    """Core controller: orchestrates the execution of three stages"""

    def __init__(self, ai_provider):
        self.sci_engine = ScientificEngine(ai_provider)
        self.vis_engine = VisualEngine(ai_provider)
        self.post_processor = PostProcessor()

    async def execute(self, concept_data: Dict, user_preferences: Dict) -> Dict:
        pipeline_start = time.time()

        # Stage 1: Scientific modeling
        scientific_model = await self.sci_engine.run(concept_data)

        # Stage 2: Page generation
        raw_html = await self.vis_engine.run(concept_data, scientific_model, user_preferences)

        # Stage 3: Post-processing
        final_html = self.post_processor.run(raw_html)

        total_time = time.time() - pipeline_start
        print(f"\n✅ Generation completed! Total time: {total_time:.1f}s")

        # Return structure remains the same
        return {
            "html": final_html,
            "scientific_analysis": scientific_model.raw_analysis,
            "metadata": {
                "title": f"交互式学习 - {concept_data.get('concept_name', '')}",
                "total_time_seconds": round(total_time, 2),
                "ai_provider": "Zhipu-Modular-Fast-Refactored"
            }
        }


class AIProcessor:
    """Main AI processor that manages different AI providers."""

    def __init__(self, provider: Optional[AIProvider] = None, provider_config: Optional[Dict] = None,
                 generation_mode: str = "fast"):
        """
        Initialize the AI processor with a specific provider.

        Args:
            provider: AIProvider instance (if None, will create from config)
            provider_config: Configuration for creating a provider
            generation_mode: HTML generation mode - "fast" (~30s) or "heavy" (~3-5min)
        """
        if provider:
            self.provider = provider
        else:
            self.provider = self._create_provider_from_config(provider_config or {})

        self.generation_mode = generation_mode

    def _create_provider_from_config(self, config: Dict) -> AIProvider:
        """Create AI provider from configuration."""
        provider_type = config.get('provider', 'english').lower()

        if provider_type in ['english', 'gemini', 'openai']:
            # Unified English provider supports both Gemini and OpenAI models
            model = config.get('model', 'gpt-4.1')

            # Default models for different provider types
            if provider_type == 'gemini':
                model = config.get('model', 'gemini-3-pro-image-preview')
            elif provider_type == 'openai':
                model = config.get('model', 'gpt-4.1')

            return EnglishProvider(
                api_key=config.get('api_key'),
                model=model
            )
        elif provider_type == 'chinese':
            # Unified Chinese provider supports both Anthropic and Zhipu models
            provider = ChineseProvider(
                api_key=config.get('api_key'),
                model=config.get('model', 'glm-4.6v'),
                base_url=config.get('base_url')
            )
            # Set text model if specified
            if config.get('text_model'):
                provider.text_model = config.get('text_model')
            return provider
        else:
            raise ValueError(f"Unsupported provider: {provider_type}. Supported providers: english (supports gemini/openai), chinese (supports anthropic/zhipu)")

    async def process_pdf_complete(self, pdf_path: str, user_preferences: Optional[Dict] = None) -> Dict:
        """
        Complete PDF processing pipeline using the configured AI provider.
        """
        processing_start = time.time()
        user_preferences = user_preferences or {}
        include_prerequisites = user_preferences.get("include_prerequisites", True)
        include_exercises = user_preferences.get("include_exercises", True)

        # Update Zhipu text model if specified in user preferences
        if hasattr(self.provider, 'text_model') and "zhipu_text_model" in user_preferences:
            self.provider.text_model = user_preferences["zhipu_text_model"]
            logger.info(f"🔄 Using Zhipu text model from user preferences: {self.provider.text_model}")

        logger.info(f"🚀 Starting PDF processing pipeline with {self.provider.get_provider_name()}")

        # Step 1: Get PDF metadata
        metadata_start = time.time()
        metadata = self.get_pdf_metadata(pdf_path)
        metadata_time = time.time() - metadata_start
        logger.info(f"📋 PDF metadata extracted in {metadata_time:.2f}s - Pages: {metadata.get('page_count', 'unknown')}")

        # Step 2: Convert PDF to images
        logger.info(f"🔄 Converting PDF to images...")
        conversion_start = time.time()
        pdf_images = self.convert_pdf_to_images(pdf_path)
        conversion_time = time.time() - conversion_start
        logger.info(f"🖼️ PDF to images conversion completed in {conversion_time:.2f}s - Generated {len(pdf_images)} images")

        # Step 3: Analyze content with AI provider
        logger.info(f"🧠 Starting AI content analysis...")
        analysis_start = time.time()
        content_analysis = await self.analyze_content_with_ai(pdf_images, user_preferences)
        if not include_prerequisites and "prerequisite_knowledge" in content_analysis:
            content_analysis = {**content_analysis}
            content_analysis.pop("prerequisite_knowledge", None)
        analysis_time = time.time() - analysis_start
        logger.info(f"📊 Content analysis completed in {analysis_time:.2f}s")

        # Step 4: Generate knowledge cards 
        if include_prerequisites:
            logger.info("🖼️ Starting knowledge card generation...")
            knowledge_cards_start = time.time()
            knowledge_cards = await self.generate_knowledge_cards(content_analysis, user_preferences)
            knowledge_cards_time = time.time() - knowledge_cards_start
            logger.info(f"🖼️ Knowledge card generation completed in {knowledge_cards_time:.2f}s")
            logger.info(f"{knowledge_cards}")

            cards = knowledge_cards.get("cards") if isinstance(knowledge_cards, dict) else None
            cards = cards if isinstance(cards, list) else []
            prerequisite_items = content_analysis.get("prerequisite_knowledge")
            prerequisite_items = prerequisite_items if isinstance(prerequisite_items, list) else []

            if not prerequisite_items and cards:
                prerequisite_items = [card.get("title") for card in cards if card.get("title")]

            if prerequisite_items:
                card_by_title = {
                    card.get("title"): card
                    for card in cards
                    if isinstance(card, dict) and card.get("title")
                }
                aligned_cards = []
                for index, item in enumerate(prerequisite_items):
                    card = card_by_title.get(item)
                    if not card and index < len(cards):
                        candidate = cards[index]
                        if isinstance(candidate, dict):
                            card = {**candidate, "title": item}
                    if not card:
                        card = {
                            "title": item,
                            "summary_md": f"**{item}**\n\n请复习该知识点的定义、关键概念和常见题型。"
                        }
                    aligned_cards.append(card)
                knowledge_cards = {"cards": aligned_cards}
                content_analysis = {**content_analysis, "prerequisite_knowledge": prerequisite_items}
            else:
                knowledge_cards = {"cards": []}
        else:
            knowledge_cards = {}

        # Step 5: Generate interactive website
        logger.info(f"🎨 Starting website generation...")
        website_start = time.time()
        website_content = await self.generate_interactive_website(
            pdf_images,
            content_analysis,
            user_preferences
        )
        if not include_exercises:
            website_content["interactive_elements"] = []
        website_time = time.time() - website_start
        logger.info(f"🌐 Website generation completed in {website_time:.2f}s")

        total_processing_time = time.time() - processing_start
        logger.info(f"✅ Complete PDF processing finished in {total_processing_time:.2f}s total")

        return {
            "status": "success",
            "metadata": metadata,
            "analysis": content_analysis,
            "knowledge_cards": knowledge_cards,
            "website": website_content,
            "processing_info": {
                "total_pages": len(pdf_images),
                "pages_processed": min(len(pdf_images), 15),
                "images_generated": len(pdf_images),
                "processing_method": f"ai-vision-{self.provider.get_provider_name().lower()}",
                "ai_provider": self.provider.get_provider_name()
            }
        }

        # except Exception as e:
        #     return {
        #         "status": "error",
        #         "error": str(e),
        #         "metadata": {},
        #         "analysis": {},
        #         "website": None,
        #         "processing_info": {
        #             "error_occurred": True,
        #             "ai_provider": self.provider.get_provider_name()
        #         }
        #     }

    async def analyze_content_with_ai(self, pdf_images: List[Dict], user_preferences: Optional[Dict] = None) -> Dict:
        """Analyze content using the configured AI provider."""
        return await self.provider.analyze_content(pdf_images, user_preferences or {})

    async def generate_interactive_website(self, pdf_images: List[Dict], analysis: Dict, user_preferences: Optional[Dict] = None, mode: Optional[str] = None) -> Dict:
        """
        Generate website using the configured AI provider and specified mode.

        Args:
            pdf_images: List of PDF page images
            analysis: Content analysis
            user_preferences: User preferences for personalization
            mode: Generation mode - "fast" or "heavy" (overrides instance setting)

        Returns:
            Dict with generated HTML and metadata
        """
        mode = mode or self.generation_mode
        user_preferences = user_preferences or {}

        # Respect user's language preference if provided, otherwise default to Chinese
        if 'language' not in user_preferences:
            user_preferences['language'] = 'zh-CN'
            user_preferences['output_language'] = '简体中文'

        # Import generators here to avoid circular imports
        from .html_generation import FastGenerator, HeavyGenerator

        try:
            if mode == "heavy":
                logger.info(f"🎨 Using Heavy Mode (2-stage pipeline) for generation")
                generator = HeavyGenerator(self.provider)
            else:
                logger.info(f"🎨 Using Fast Mode (one-shot) for generation")
                generator = FastGenerator(self.provider)

            result = await generator.generate(pdf_images, analysis, user_preferences)
            result["mode_used"] = mode
            return result

        except Exception as e:
            logger.error(f"❌ Generator failed: {e}, falling back to provider method")
            # Fallback to original provider method
            return await self.provider.generate_website(pdf_images, analysis, user_preferences)

    async def modify_website_ui(self, original_html: str, user_prompt: str, document_context: Dict) -> Dict:
        """Modify website UI using the configured AI provider."""
        return await self.provider.modify_website_ui(original_html, user_prompt, document_context)

    async def generate_knowledge_cards(self, analysis: Dict, user_preferences: Optional[Dict] = None) -> Dict:
        """Generate prerequisite knowledge cards using the configured AI provider."""
        return await self.provider.generate_knowledge_cards(analysis, user_preferences or {})

    async def process_concept_complete(self, concept_data: Dict, user_preferences: Optional[Dict] = None) -> Dict:
        """
        Process concept input and generate interactive learning website.
        This is an alternative to PDF processing that works directly with text-based concept descriptions.
        """
        processing_start = time.time()
        user_preferences = user_preferences or {}
        include_exercises = user_preferences.get("include_exercises", True)
        logger.info(f"🚀 Starting concept processing pipeline with {self.provider.get_provider_name()}")
        logger.info(f"📝 Concept: {concept_data.get('subject')} - {concept_data.get('concept_name')}")

        try:
            # Generate interactive website directly from concept
            logger.info(f"🎨 Starting website generation from concept...")
            website_start = time.time()
            website_content = await self.generate_website_from_concept(
                concept_data,
                user_preferences
            )
            if not include_exercises:
                website_content["interactive_elements"] = []
            website_time = time.time() - website_start
            logger.info(f"🌐 Website generation completed in {website_time:.2f}s")

            total_processing_time = time.time() - processing_start
            logger.info(f"✅ Complete concept processing finished in {total_processing_time:.2f}s total")

            # Create metadata for concept-based document
            metadata = {
                "title": concept_data.get('concept_name', 'Concept Learning'),
                "subject": concept_data.get('subject', ''),
                "concept_overview": concept_data.get('concept_overview', ''),
                "page_count": 1,
                "source_type": "concept_input"
            }

            # Create analysis from concept data
            analysis = {
                "main_topics": [concept_data.get('concept_name', '')],
                "key_concepts": concept_data.get('mastery_points', []).split('\n') if concept_data.get('mastery_points') else [],
                "learning_objectives": concept_data.get('mastery_points', []).split('\n') if concept_data.get('mastery_points') else [],
                "subject_area": concept_data.get('subject', ''),
                "difficulty_level": "intermediate"
            }

            return {
                "status": "success",
                "metadata": metadata,
                "analysis": analysis,
                "website": website_content,
                "processing_info": {
                    "total_pages": 1,
                    "pages_processed": 1,
                    "processing_method": f"concept-ai-{self.provider.get_provider_name().lower()}",
                    "ai_provider": self.provider.get_provider_name(),
                    "concept_data": concept_data
                }
            }

        except Exception as e:
            logger.error(f"❌ Error processing concept: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "metadata": {},
                "analysis": {},
                "website": None,
                "processing_info": {
                    "error_occurred": True,
                    "ai_provider": self.provider.get_provider_name()
                }
            }

    async def generate_website_from_concept(self, concept_data: Dict, user_preferences: Optional[Dict] = None) -> Dict:
        """Generate website from concept using the configured AI provider."""
        user_preferences = user_preferences or {}

        # Update Zhipu text model if specified in user preferences
        if hasattr(self.provider, 'text_model') and "zhipu_text_model" in user_preferences:
            self.provider.text_model = user_preferences["zhipu_text_model"]
            logger.info(f"🔄 Using Zhipu text model from user preferences: {self.provider.text_model}")

        return await self.provider.generate_website_from_concept(concept_data, user_preferences)

    def get_pdf_metadata(self, pdf_path: str) -> Dict:
        """Extract basic metadata from PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata = {
                    "title": pdf_reader.metadata.get('/Title', 'Unknown'),
                    "author": pdf_reader.metadata.get('/Author', 'Unknown'),
                    "subject": pdf_reader.metadata.get('/Subject', ''),
                    "creator": pdf_reader.metadata.get('/Creator', ''),
                    "producer": pdf_reader.metadata.get('/Producer', ''),
                    "creation_date": str(pdf_reader.metadata.get('/CreationDate', '')),
                    "modification_date": str(pdf_reader.metadata.get('/ModDate', '')),
                    "page_count": len(pdf_reader.pages)
                }
                return metadata
        except Exception as e:
            print(f"Error extracting PDF metadata: {e}")
            return {"page_count": 0, "title": "Unknown"}

    def convert_pdf_to_images(self, pdf_path: str) -> List[Dict]:
        """Convert PDF pages to images using PyMuPDF."""
        try:
            if PYMUPDF_AVAILABLE:
                # Use PyMuPDF (no external dependencies)
                try:
                    return self._convert_with_pymupdf(pdf_path)
                except Exception as pymupdf_error:
                    print(f"PyMuPDF failed ({pymupdf_error}), using text fallback")
                    return self._create_text_based_representation(pdf_path)
            else:
                # PyMuPDF not available - fallback
                print("PyMuPDF not available, using fallback method")
                return self._create_text_based_representation(pdf_path)

        except Exception as e:
            raise Exception(f"Error converting PDF to images: {str(e)}")

    def _convert_with_pymupdf(self, pdf_path: str) -> List[Dict]:
        """Convert PDF to images using PyMuPDF (preferred method)."""
        try:
            doc_open_start = time.time()
            doc = fitz.open(pdf_path)
            doc_open_time = time.time() - doc_open_start
            logger.info(f"📖 PDF opened with PyMuPDF in {doc_open_time:.2f}s - {len(doc)} pages")

            processed_images = []
            processing_start = time.time()

            for page_num in range(len(doc)):
                page_start = time.time()
                page = doc[page_num]

                # Render page to pixmap with good quality
                render_start = time.time()
                pix = page.get_pixmap(dpi=200)
                render_time = time.time() - render_start

                # Convert pixmap to PIL Image
                convert_start = time.time()
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                convert_time = time.time() - convert_start

                # Convert PIL image to base64
                encode_start = time.time()
                buffered = io.BytesIO()
                image.save(buffered, format="PNG", quality=90)
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                encode_time = time.time() - encode_start

                processed_images.append({
                    "page": page_num + 1,
                    "image_data": img_base64,
                    "format": "PNG",
                    "width": pix.width,
                    "height": pix.height
                })

            doc.close()
            return processed_images

        except Exception as e:
            logger.error(f"❌ PyMuPDF conversion failed: {str(e)}")
            raise Exception(f"PyMuPDF conversion failed: {str(e)}")

  
    def _create_text_based_representation(self, pdf_path: str) -> List[Dict]:
        """Create a text-based representation of PDF pages when image conversion is not available."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                processed_images = []

                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()

                    # Create a simple text-based "image" representation
                    img = Image.new('RGB', (800, 1000), color='white')
                    from PIL import ImageDraw, ImageFont

                    draw = ImageDraw.Draw(img)

                    try:
                        font = ImageFont.load_default()
                    except:
                        font = None

                    # Add title
                    draw.text((50, 50), f"Page {page_num + 1}", fill='black', font=font)

                    # Add extracted text (truncated)
                    y_offset = 100
                    for line in text.split('\n')[:30]:  # Limit lines
                        if y_offset < 900:  # Leave margin at bottom
                            # Truncate long lines
                            if len(line) > 80:
                                line = line[:77] + "..."
                            draw.text((50, y_offset), line, fill='black', font=font)
                            y_offset += 30

                    # Convert to base64
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG", quality=85)
                    img_base64 = base64.b64encode(buffered.getvalue()).decode()

                    processed_images.append({
                        "page": page_num + 1,
                        "image_data": img_base64,
                        "format": "JPEG",
                        "width": 800,
                        "height": 1000,
                        "is_fallback": True
                    })

                return processed_images

        except Exception as e:
            raise Exception(f"Error creating text-based representation: {str(e)}")

    async def search_templates_for_user(
        self,
        content_info: Dict,
        workflow_type: str,
        db_session_factory,
        max_results: int = 5
    ) -> Dict:
        """
        Step 1: Search templates for user selection.

        Returns template options that user can review and choose from.
        """
        from .template_registry import get_template_registry

        registry = get_template_registry(db_session_factory)

        template_options = registry.search_templates_for_user_selection(
            content_info=content_info,
            workflow_type=workflow_type,
            max_results=max_results
        )

        return {
            "status": "success",
            "workflow_type": workflow_type,
            "templates_found": len(template_options),
            "template_options": template_options
        }

    async def generate_with_selected_template(
        self,
        template_id: str,
        content_info: Dict,
        user_preferences: Dict,
        workflow_type: str,
        db_session_factory,
        customization_params: Optional[Dict] = None
    ) -> Dict:
        """
        Step 2: Generate using user-selected template.
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"=" * 80)
        logger.info(f"AI_PROCESSOR: generate_with_selected_template called")
        logger.info(f"Template ID: {template_id}")
        logger.info(f"Workflow type: {workflow_type}")
        logger.info(f"Content info: {content_info}")
        logger.info(f"User preferences: {user_preferences}")
        logger.info(f"=" * 80)

        from .template_registry import get_template_registry

        logger.info(f"Getting template registry...")
        registry = get_template_registry(db_session_factory)

        logger.info(f"Getting template by ID: {template_id}")
        template = registry.get_template_by_id(template_id)

        if not template:
            logger.error(f"Template not found: {template_id}")
            return {"status": "error", "error": f"Template not found: {template_id}"}

        logger.info(f"Template found: {template.display_name}")
        logger.info(f"Calling provider.customize_template...")

        # Customize template using LLM
        customized_html = await self.provider.customize_template(
            template=template,
            content_info=content_info,
            user_preferences=user_preferences,
            customization_params=customization_params
        )

        logger.info(f"Customization completed. HTML length: {len(customized_html) if customized_html else 0}")

        # Update template usage count
        logger.info(f"Updating template usage count...")
        registry.update_template_usage(template_id)
        logger.info(f"Template usage count updated")

        logger.info(f"Returning success response")

        return {
            "status": "success",
            "html": customized_html,
            "metadata": {
                "template_used": template_id,
                "template_name": template.display_name,
                "generation_method": "template_based"
            }
        }

    async def generate_without_template(
        self,
        content_info: Dict,
        user_preferences: Dict,
        workflow_type: str
    ) -> Dict:
        """
        Fallback: Generate without template (pure AI).
        """
        if workflow_type == 'website_pdf':
            # This would need images and analysis from content_info
            return await self.provider.generate_website(
                images=content_info.get('images', []),
                analysis=content_info.get('analysis', {}),
                user_preferences=user_preferences
            )
        elif workflow_type == 'website_concept':
            return await self.provider.generate_website_from_concept(
                concept_data=content_info,
                user_preferences=user_preferences
            )
        else:
            return {"status": "error", "error": f"Unsupported workflow type: {workflow_type}"}

    def get_provider_name(self) -> str:
        """Get the name of the current AI provider."""
        return self.provider.get_provider_name()

    def get_provider_info(self) -> Dict:
        """Get information about the current AI provider."""
        return {
            "provider": self.get_provider_name(),
            "available_providers": self._get_available_providers()
        }

    def _get_available_providers(self) -> List[str]:
        """Get list of available AI providers."""
        available = ["english"]  # English provider is always available (uses httpx)
        if ZHIPU_AVAILABLE:
            available.append("zhipu")
        if ANTHROPIC_AVAILABLE:
            available.append("anthropic")
        return available


# Global AI processor instance
_ai_processor_instance = None

def get_ai_processor():
    """
    Get or create the global AI processor instance.

    This is a convenience function that creates a singleton AI processor
    using environment variables for configuration.

    Returns:
        AIProcessor: The global AI processor instance

    Raises:
        ValueError: If no API keys are configured
    """
    global _ai_processor_instance

    if _ai_processor_instance is None:
        # Determine which provider to use based on available API keys
        provider_config = {}

        # Check for Zhipu API key (preferred for Chinese content and PPT processing)
        zhipu_api_key = os.getenv("ZHIPU_API_KEY")
        if zhipu_api_key:
            provider_config = {
                'provider': 'zhipu',
                'api_key': zhipu_api_key,
                'model': 'glm-4.6v'
            }
            logger.info("Using Zhipu AI provider")
        else:
            # Check for Anthropic API key
            anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
            if anthropic_api_key:
                model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
                provider_config = {
                    'provider': 'anthropic',
                    'api_key': anthropic_api_key,
                    'base_url': os.getenv("ANTHROPIC_BASE_URL"),
                    'model': model
                }
                logger.info(f"Using Anthropic provider with model {model}")
            else:
                # Check for English API keys
                english_api_key = (
                    os.getenv("ENGLISH_API_KEY") or
                    os.getenv("MIDDLE_TRANSFER_API_KEY") or
                    os.getenv("GEMINI_API_KEY") or
                    os.getenv("OPENAI_API_KEY")
                )
                if english_api_key:
                    # Determine model based on available keys
                    model = os.getenv("ENGLISH_MODEL", "gpt-4.1")
                    if os.getenv("GEMINI_API_KEY"):
                        model = "gemini-3-pro-image-preview"

                    provider_config = {
                        'provider': 'english',
                        'api_key': english_api_key,
                        'model': model
                    }
                    logger.info(f"Using English provider with model {model}")
                else:
                    raise ValueError(
                        "No AI provider API key found. Please set one of:\n"
                        "- ZHIPU_API_KEY (recommended for PPT processing)\n"
                        "- ANTHROPIC_API_KEY\n"
                        "- ENGLISH_API_KEY\n"
                        "- MIDDLE_TRANSFER_API_KEY\n"
                        "- GEMINI_API_KEY\n"
                        "- OPENAI_API_KEY"
                    )

        _ai_processor_instance = AIProcessor(provider_config=provider_config)

    return _ai_processor_instance
