"""
Editor Processor - Specialized AI service for WebEditor HTML modifications.
This module provides AI-powered HTML editing capabilities specifically for the WebEditor component.
Uses Zhipu AI for intelligent HTML modifications based on user citations and prompts.
"""

from typing import Dict, List, Optional, Any
import os
import time
import asyncio
import logging
import re

# Import segmented reading and diff modification modules
from .read import build_full_content_prompt
from .modify import apply_unified_diff, UnifiedDiffParser

# Configure logging
logger = logging.getLogger(__name__)

# Import Zhipu AI provider
try:
    from zai import ZhipuAiClient
    ZHIPU_AVAILABLE = True
except ImportError:
    ZHIPU_AVAILABLE = False
    logger.warning("Zhipu AI SDK not available. Install with: pip install zai-sdk")

# Import Anthropic AI provider
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic SDK not available. Install with: pip install anthropic")


class ChineseEditorProvider:
    """Unified Chinese AI provider for HTML editing, supporting both Anthropic and Zhipu models."""

    # Model detection
    ANTHROPIC_MODELS = ["claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5-20251001"]
    ZHIPU_MODELS = ["glm-4.7", "glm-4.6"]

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "glm-4.7",
        base_url: Optional[str] = None
    ):
        """
        Initialize the Chinese Editor Provider.

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
            logger.info(f"🎨 ChineseEditorProvider initialized with Anthropic backend, model: {self.model}")
        else:  # zhipu
            if not ZHIPU_AVAILABLE:
                raise ImportError("Zhipu AI SDK not installed. Install with: pip install zai-sdk")

            self.zhipu_client = ZhipuAiClient(api_key=api_key)
            self.anthropic_client = None
            logger.info(f"🎨 ChineseEditorProvider initialized with Zhipu backend, model: {self.model}")

    def _detect_backend(self, model: str) -> str:
        """Detect which backend to use based on model name."""
        if model.startswith("claude-") or model in self.ANTHROPIC_MODELS:
            return "anthropic"
        return "zhipu"  # Default to Zhipu

    def _format_citations(self, citations: List[Dict], original_html: str = "") -> str:
        """
        Format citations into a readable text for the AI prompt.
        When original_html is provided, includes the line number of the cited element
        to help the AI precisely locate the specific element instance.

        Args:
            citations: List of citation dictionaries
            original_html: Original HTML content for line number lookup

        Returns:
            Formatted citations text
        """
        citation_parts = []
        for c in citations:
            html_preview = c.get('html', '')[:500]
            if len(c.get('html', '')) > 500:
                html_preview += '...'

            # Try to find the line number of this citation in the original HTML
            line_info = ""
            if original_html and c.get('html'):
                line_number = self._find_citation_line_number(
                    original_html, c.get('html', ''), c.get('selector', '')
                )
                if line_number:
                    line_info = f"\n  所在行号: 第 {line_number} 行（仅修改此行的元素，不要修改其他同类型元素）"

            citation_text = (
                f"引用 {c.get('index', '?')}:\n"
                f"  选择器: {c.get('selector', 'unknown')}\n"
                f"  HTML片段: {html_preview}"
                f"{line_info}\n"
                f"  用户备注: {c.get('note', '无')}"
            )
            citation_parts.append(citation_text)

        return "\n\n".join(citation_parts)

    @staticmethod
    def _find_citation_line_number(original_html: str, citation_html: str, selector: str = "") -> Optional[int]:
        """
        Find the line number of a cited HTML fragment within the original HTML.

        Args:
            original_html: Full HTML content
            citation_html: HTML fragment from the citation
            selector: CSS selector hint for disambiguation

        Returns:
            1-indexed line number, or None if not found
        """
        if not citation_html:
            return None

        # Clean up the citation HTML for matching (take first line / tag)
        search_text = citation_html.strip().split('\n')[0].strip()
        if not search_text:
            return None

        lines = original_html.split('\n')
        for i, line in enumerate(lines):
            if search_text in line:
                return i + 1  # 1-indexed

        # Fallback: try matching just the tag opening
        tag_match = re.match(r'<(\w+)[^>]*>', search_text)
        if tag_match:
            tag_opening = tag_match.group(0)
            for i, line in enumerate(lines):
                if tag_opening in line:
                    return i + 1

        return None

    def _extract_html_from_response(self, content_text: str, fallback_html: str) -> str:
        """
        Extract HTML content from AI response.

        First tries to extract and apply unified diff.
        Falls back to extracting full HTML if no diff found.

        Args:
            content_text: Raw response text from AI
            fallback_html: Fallback HTML to return if extraction fails

        Returns:
            Extracted/modified HTML content
        """
        # First, try to extract and apply unified diff
        diff_content = UnifiedDiffParser.extract_diff_from_response(content_text)
        if diff_content:
            logger.info("📝 Found unified diff in AI response, applying...")
            result = apply_unified_diff(fallback_html, diff_content)

            if result["status"] == "success":
                hunks_applied = result.get("hunks_applied", 0)
                total_hunks = result.get("total_hunks", 0)
                logger.info(f"✅ Applied unified diff: {hunks_applied}/{total_hunks} hunks")
                return result["modified_html"]
            else:
                logger.warning(f"⚠️ Failed to apply diff: {result.get('error')}")
                # Fall through to try extracting full HTML

        # Try to find DOCTYPE declaration (full HTML response)
        html_start = content_text.find('<!DOCTYPE html>')
        if html_start == -1:
            html_start = content_text.find('<!doctype html>')
        if html_start == -1:
            html_start = content_text.find('<html')

        html_end = content_text.rfind('</html>')
        if html_end != -1:
            html_end += 7  # Include '</html>'

        if html_start != -1 and html_end > html_start:
            logger.info("📄 Extracted full HTML from AI response")
            return content_text[html_start:html_end]

        # If no proper HTML structure found, check if the response is mostly HTML
        if '<html' in content_text.lower() and '</html>' in content_text.lower():
            return content_text.strip()

        # Return fallback if no valid HTML found
        logger.warning("⚠️ Could not extract valid HTML from AI response, using fallback")
        return fallback_html

    async def _run_zhipu_call(self, model: str, messages: List[Dict], thinking_params: Optional[Dict] = None) -> Any:
        """Run synchronous Zhipu API call in a thread pool to avoid blocking the event loop."""
        if self.zhipu_client is None:
            raise RuntimeError("Zhipu client not initialized. This provider is configured for Anthropic.")

        def _make_sync_call():
            params = {
                "model": model,
                "messages": messages
            }
            if thinking_params:
                params["thinking"] = thinking_params

            return self.zhipu_client.chat.completions.create(**params)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _make_sync_call)

    async def _run_anthropic_call(self, model: str, messages: List[Dict], max_tokens: int = 16000, thinking_enabled: bool = False) -> Any:
        """Run synchronous Anthropic API call in a thread pool to avoid blocking the event loop."""
        if self.anthropic_client is None:
            raise RuntimeError("Anthropic client not initialized. This provider is configured for Zhipu.")

        def _make_sync_call():
            params = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": messages
            }
            if thinking_enabled and "claude-3-7" in model:
                params["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": 4096
                }

            return self.anthropic_client.messages.create(**params)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _make_sync_call)

    async def modify_html_with_citations(
        self,
        original_html: str,
        citations: List[Dict],
        user_prompt: str,
        thinking_enabled: Optional[bool] = None
    ) -> Dict:
        """
        Modify HTML using the appropriate backend.

        Args:
            original_html: The original HTML content to modify
            citations: List of citation dictionaries
            user_prompt: User's modification instructions
            thinking_enabled: Whether to enable thinking mode

        Returns:
            Dict containing status, modified_html, and optional error
        """
        modification_start = time.time()
        logger.info(f"🎨 Starting HTML modification with ChineseEditorProvider ({self.backend}) {self.model}")
        logger.info(f"是否开启思考模式: {'是' if thinking_enabled else '否'}")
        logger.info(f"📋 Citations count: {len(citations)}")
        logger.info(f"📋 Citations content: {citations}")
        logger.info(f"📝 User prompt: {user_prompt[:100]}{'...' if len(user_prompt) > 100 else ''}")

        try:
            citations_text = self._format_citations(citations, original_html)
            prompt = build_full_content_prompt(original_html, citations_text, user_prompt)

            logger.info(f"🔄 Calling {self.backend} AI to modify HTML...")
            ai_start = time.time()

            if self.backend == "anthropic":
                response = await self._run_anthropic_call(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    thinking_enabled=thinking_enabled or False
                )
                ai_time = time.time() - ai_start
                logger.info(f"✅ Anthropic AI response received in {ai_time:.2f}s")

                if response and response.content:
                    content_text = ""
                    for block in response.content:
                        if hasattr(block, 'text'):
                            content_text += block.text
                else:
                    content_text = ""
            else:  # zhipu
                response = await self._run_zhipu_call(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    thinking_params={"type": "enabled" if thinking_enabled else "disabled"}
                )
                ai_time = time.time() - ai_start
                logger.info(f"✅ Zhipu AI response received in {ai_time:.2f}s")

                if response and response.choices and response.choices[0].message:
                    content_text = response.choices[0].message.content
                else:
                    content_text = ""

            if content_text:
                modified_html = self._extract_html_from_response(content_text, original_html)

                total_modification_time = time.time() - modification_start
                logger.info(f"✅ HTML modification completed in {total_modification_time:.2f}s total")
                logger.info(f"📊 Modified HTML length: {len(modified_html)} characters")

                return {
                    "status": "success",
                    "modified_html": modified_html
                }

            logger.warning(f"⚠️ No valid response from {self.backend} AI, using original HTML as fallback")
            return {
                "status": "success",
                "modified_html": original_html
            }

        except Exception as e:
            logger.error(f"❌ Error modifying HTML with {self.backend}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "modified_html": original_html
            }

    def get_provider_name(self) -> str:
        """Get the name of the AI provider."""
        if self.backend == "anthropic":
            return f"ChineseEditorProvider-Anthropic ({self.model})"
        return f"ChineseEditorProvider-Zhipu ({self.model})"


class EditorProcessor:
    """
    AI processor specifically designed for WebEditor HTML modifications.
    Supports multiple AI providers through the unified ChineseEditorProvider for intelligent HTML editing
    based on user citations and prompts.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        provider_type: str = "chinese",
        base_url: Optional[str] = None
    ):
        """
        Initialize the EditorProcessor.

        Args:
            api_key: API key for the selected provider
            model: Model to use (defaults depend on backend, auto-detected from model name)
            provider_type: Provider type - "chinese" (supports both anthropic and zhipu models)
            base_url: Optional base URL for API proxy (Anthropic backend only)
        """
        provider_type = provider_type.lower()

        if provider_type == "chinese":
            # Unified Chinese provider - auto-detects backend from model name
            default_model = model or "glm-4.7"
            self.provider = ChineseEditorProvider(
                api_key=api_key,
                model=default_model,
                base_url=base_url
            )
        else:
            raise ValueError(f"Unknown provider type: {provider_type}. Supported: 'chinese'")

        logger.info(f"🎨 EditorProcessor initialized with provider: {self.provider.get_provider_name()}")

    async def modify_html_with_citations(
        self,
        original_html: str,
        citations: List[Dict],
        user_prompt: str,
        thinking_enabled: Optional[bool] = None
    ) -> Dict:
        """
        Modify HTML based on user-selected citations and modification instructions.

        Args:
            original_html: The original HTML content to modify
            citations: List of citation dictionaries containing:
                - index: Citation index number
                - selector: CSS selector for the element
                - html: HTML content of the selected element
                - note: Optional user note for this citation
            user_prompt: User's modification instructions
            thinking_enabled: Whether to enable thinking mode

        Returns:
            Dict containing:
                - status: "success" or "error"
                - modified_html: The modified HTML content
                - error: Error message if status is "error"
        """
        return await self.provider.modify_html_with_citations(
            original_html=original_html,
            citations=citations,
            user_prompt=user_prompt,
            thinking_enabled=thinking_enabled
        )

    def get_processor_info(self) -> Dict:
        """
        Get information about this processor.

        Returns:
            Dict containing processor information
        """
        return {
            "name": "EditorProcessor",
            "provider": self.provider.get_provider_name(),
            "capabilities": ["html_modification", "citation_based_editing", "unified_diff"],
            "zhipu_available": ZHIPU_AVAILABLE,
            "anthropic_available": ANTHROPIC_AVAILABLE
        }

    def get_provider_name(self) -> str:
        """Get the name of the current AI provider."""
        return self.provider.get_provider_name()


# Global EditorProcessor instance
_editor_processor_instance = None


# Model to provider mapping
CHINESE_MODELS = ["claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5-20251001",
                  "glm-4.7", "glm-4.6"]


def get_editor_processor(
    provider_type: Optional[str] = None,
    model: Optional[str] = None
) -> EditorProcessor:
    """
    Get or create an EditorProcessor instance.

    If model is specified, creates a new instance with that model.
    Otherwise, returns a cached global instance using environment variable configuration.

    Supported models (all use unified ChineseEditorProvider with auto-detected backend):
    - Anthropic backend: claude-sonnet-4-6, claude-opus-4-6, claude-haiku-4-5-20251001
    - Zhipu backend: glm-4.7, glm-4.6

    Environment variables:
    - EDITOR_PROVIDER: Provider type - "chinese" (default: chinese)
    - ZHIPU_API_KEY: Required if using Zhipu models
    - ANTHROPIC_API_KEY: Required if using Anthropic models
    - ANTHROPIC_BASE_URL: Optional base URL for Anthropic API proxy
    - EDITOR_MODEL: Optional model name (defaults to glm-4.7)

    Args:
        provider_type: Override for provider type (only 'chinese' supported).
        model: Specific model to use. Backend is auto-detected from the model name.

    Returns:
        EditorProcessor: An EditorProcessor instance

    Raises:
        ValueError: If required API key is not configured
    """
    global _editor_processor_instance

    # If model is specified, create a new instance with that model
    if model is not None:
        return _create_editor_processor(model)

    # Determine the selected provider (for backwards compatibility, but only 'chinese' is supported)
    selected_provider = (provider_type or os.getenv("EDITOR_PROVIDER", "chinese")).lower()

    # If provider_type is explicitly specified, always create a new instance
    if provider_type is not None:
        return _create_editor_processor(model=os.getenv("EDITOR_MODEL", "glm-4.7"))

    # Use cached global instance if no specific provider requested
    if _editor_processor_instance is None:
        _editor_processor_instance = _create_editor_processor(model=os.getenv("EDITOR_MODEL", "glm-4.7"))
        logger.info(f"🎨 Global EditorProcessor instance created with provider: {_editor_processor_instance.get_provider_name()}")

    return _editor_processor_instance


def _create_editor_processor(
    model: Optional[str] = None
) -> EditorProcessor:
    """
    Create a new EditorProcessor instance with the specified model.
    The backend (Anthropic vs Zhipu) is auto-detected from the model name.

    Args:
        model: Specific model to use. Defaults to glm-4.7.

    Returns:
        EditorProcessor: A new EditorProcessor instance

    Raises:
        ValueError: If required API key is not configured
    """
    final_model = model or os.getenv("EDITOR_MODEL", "glm-4.7")

    # Determine API key based on model name (auto-detect backend)
    if final_model.startswith("claude-") or final_model in ["claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5-20251001"]:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is not configured. "
                "Please set ANTHROPIC_API_KEY to use Anthropic models."
            )
        base_url = os.getenv("ANTHROPIC_BASE_URL")
    else:
        api_key = os.getenv("ZHIPU_API_KEY")
        if not api_key:
            raise ValueError(
                "ZHIPU_API_KEY environment variable is not configured. "
                "Please set ZHIPU_API_KEY to use Zhipu models."
            )
        base_url = None

    return EditorProcessor(
        api_key=api_key,
        model=final_model,
        provider_type="chinese",
        base_url=base_url
    )


def reset_editor_processor() -> None:
    """
    Reset the global EditorProcessor instance.
    Useful for testing or when configuration changes.
    """
    global _editor_processor_instance
    _editor_processor_instance = None
    logger.info("🔄 Global EditorProcessor instance reset")
