"""
HTML Content Reader - Segmented reading for large HTML files.

Inspired by opencode's read.ts, this module provides:
- Offset/limit based segmented reading
- Max bytes cap to prevent context overflow
- Line number annotations for precise editing
- Truncation hints for continuation

This allows AI models to read HTML content in manageable chunks
rather than receiving the entire file at once.
"""

from typing import Dict, Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

# Constants matching read.ts design
DEFAULT_READ_LIMIT = 2000       # Default max lines per read
MAX_LINE_LENGTH = 2000          # Truncate lines longer than this
MAX_LINE_SUFFIX = f"... (line truncated to {MAX_LINE_LENGTH} chars)"
MAX_BYTES = 50 * 1024           # 50 KB max per read
MAX_BYTES_LABEL = f"{MAX_BYTES // 1024} KB"


class HTMLReader:
    """
    Segmented HTML content reader.

    Reads HTML content in chunks with line-number annotations,
    enabling AI models to reference specific lines for precise editing.
    """

    def __init__(self, content: str):
        """
        Initialize with HTML content string.

        Args:
            content: Full HTML content to be read in segments
        """
        self._content = content
        self._lines = content.splitlines(keepends=True)
        self._total_lines = len(self._lines)
        logger.info(f"📖 HTMLReader initialized: {self._total_lines} lines, "
                     f"{len(content)} chars")

    @property
    def total_lines(self) -> int:
        """Total number of lines in the content."""
        return self._total_lines

    @property
    def total_chars(self) -> int:
        """Total character count."""
        return len(self._content)

    @property
    def full_content(self) -> str:
        """Return the full original content."""
        return self._content

    def read(
        self,
        offset: int = 1,
        limit: Optional[int] = None
    ) -> Dict:
        """
        Read a segment of the HTML content with line numbers.

        Mimics read.ts behavior:
        - Lines are 1-indexed
        - Each line is prefixed with its line number
        - Long lines are truncated
        - Output is capped at MAX_BYTES
        - Returns truncation info and next offset

        Args:
            offset: Line number to start reading from (1-indexed, default 1)
            limit: Maximum number of lines to read (default DEFAULT_READ_LIMIT)

        Returns:
            Dict with:
                - content: Line-numbered content string
                - offset: Starting line number used
                - limit: Limit used
                - lines_read: Number of lines actually read
                - total_lines: Total lines in the file
                - last_line: Last line number read
                - next_offset: Next offset for continuation (None if EOF)
                - truncated: Whether output was truncated
                - truncated_by_bytes: Whether truncation was due to bytes cap
                - has_more: Whether there are more lines after this segment
        """
        if offset < 1:
            raise ValueError("offset must be >= 1")

        if limit is None:
            limit = DEFAULT_READ_LIMIT

        start = offset - 1  # Convert to 0-indexed

        if start >= self._total_lines and not (self._total_lines == 0 and offset == 1):
            raise ValueError(
                f"Offset {offset} is out of range for this content "
                f"({self._total_lines} lines)"
            )

        raw_lines: List[str] = []
        byte_count = 0
        truncated_by_bytes = False
        has_more = False
        lines_scanned = 0

        for i in range(start, self._total_lines):
            lines_scanned += 1

            if len(raw_lines) >= limit:
                has_more = True
                break

            # Get line, strip trailing newline for processing
            line = self._lines[i].rstrip('\n').rstrip('\r')

            # Truncate overly long lines
            if len(line) > MAX_LINE_LENGTH:
                line = line[:MAX_LINE_LENGTH] + MAX_LINE_SUFFIX

            # Check byte size
            line_bytes = len(line.encode('utf-8')) + (1 if raw_lines else 0)
            if byte_count + line_bytes > MAX_BYTES:
                truncated_by_bytes = True
                has_more = True
                break

            raw_lines.append(line)
            byte_count += line_bytes

        # Check if there's more content beyond what we read
        if not has_more and (start + len(raw_lines)) < self._total_lines:
            has_more = True

        # Build numbered content (matching read.ts format)
        numbered_lines = []
        for idx, line in enumerate(raw_lines):
            line_num = offset + idx
            numbered_lines.append(f"{line_num}: {line}")

        content = "\n".join(numbered_lines)

        last_line = offset + len(raw_lines) - 1 if raw_lines else offset
        next_offset = last_line + 1 if has_more else None
        truncated = has_more or truncated_by_bytes

        # Build status message (matching read.ts output format)
        if truncated_by_bytes:
            status = (f"(Output capped at {MAX_BYTES_LABEL}. "
                      f"Showing lines {offset}-{last_line}. "
                      f"Use offset={next_offset} to continue.)")
        elif has_more:
            status = (f"(Showing lines {offset}-{last_line} of "
                      f"{self._total_lines}. "
                      f"Use offset={next_offset} to continue.)")
        else:
            status = f"(End of file - total {self._total_lines} lines)"

        logger.debug(f"📖 Read lines {offset}-{last_line} of {self._total_lines} "
                     f"({len(raw_lines)} lines, {byte_count} bytes, "
                     f"truncated={truncated})")

        return {
            "content": content,
            "status": status,
            "offset": offset,
            "limit": limit,
            "lines_read": len(raw_lines),
            "total_lines": self._total_lines,
            "last_line": last_line,
            "next_offset": next_offset,
            "truncated": truncated,
            "truncated_by_bytes": truncated_by_bytes,
            "has_more": has_more
        }

    def read_all_segments(
        self,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Read the entire content in sequential segments.

        Useful for building a full segmented view of the content
        for AI processing.

        Args:
            limit: Lines per segment (default DEFAULT_READ_LIMIT)

        Returns:
            List of segment dicts from read()
        """
        segments = []
        offset = 1

        while True:
            segment = self.read(offset=offset, limit=limit)
            segments.append(segment)

            if segment["next_offset"] is None:
                break
            offset = segment["next_offset"]

        logger.info(f"📖 Read all content in {len(segments)} segment(s)")
        return segments

    def read_around_line(
        self,
        target_line: int,
        context_lines: int = 20
    ) -> Dict:
        """
        Read content around a specific line (for targeted reading).

        Args:
            target_line: The line number to center on (1-indexed)
            context_lines: Number of context lines before and after

        Returns:
            Segment dict from read()
        """
        start = max(1, target_line - context_lines)
        limit = context_lines * 2 + 1
        return self.read(offset=start, limit=limit)


def build_segmented_prompt(
    html_content: str,
    citations_text: str,
    user_prompt: str,
    max_segment_bytes: int = MAX_BYTES
) -> Tuple[str, HTMLReader]:
    """
    Build an AI prompt with segmented HTML content.

    Instead of sending the entire HTML at once, this creates a prompt
    with line-numbered content that can be sent in segments.

    For content that fits in one segment, it sends the full content.
    For larger content, it provides the first segment with instructions
    for the AI to request more via offset.

    Args:
        html_content: Full HTML content
        citations_text: Formatted citations text
        user_prompt: User's modification instructions
        max_segment_bytes: Max bytes per segment

    Returns:
        Tuple of (prompt_string, HTMLReader_instance)
    """
    reader = HTMLReader(html_content)

    # Read first segment
    first_segment = reader.read(offset=1)

    prompt = f"""你是一个专业的UI/UX专家和前端开发者。请根据用户选择的HTML元素引用和修改指示，对提供的网页HTML代码进行精确修改。

## 用户选择的HTML元素引用

用户在网页中选择了以下元素作为修改的参考点：

{citations_text}

## 用户的修改指示

{user_prompt}

## HTML源代码（带行号）

以下HTML代码标注了行号以便精确定位修改位置。

```
{first_segment['content']}
```

{first_segment['status']}

## 修改要求

1. **精确定位**：根据用户提供的选择器和HTML片段，以及行号标注，准确定位需要修改的元素
2. **使用 unified diff 格式输出修改**：不要返回完整HTML，而是只返回修改部分的 unified diff
3. **保留功能**：尽量保留原有的交互功能和样式
4. **最小化修改**：只修改必要的部分，不要改动无关代码

## 输出格式要求

请以 unified diff 格式输出你的修改，可以包含多个修改块（hunk），每个修改块使用以下格式：

```diff
--- original
+++ modified
@@ -起始行号,行数 +起始行号,行数 @@
 上下文行（不变的行）
-被删除的行
+新增的行
 上下文行（不变的行）

 @@ -起始行号,行数 +起始行号,行数 @@
 上下文行（不变的行）
-被删除的行
+新增的行
 上下文行（不变的行）
```

注意事项：
- 每个修改块至少包含3行上下文（不变的行）
- 行号必须与上方HTML源代码中的行号对应
- 可以包含多个 @@ 修改块
- 不要输出任何修改之外的解释文字

请直接输出 unified diff 内容，以 ```diff 开头，以 ``` 结尾。"""

    return prompt, reader


def build_full_content_prompt(
    html_content: str,
    citations_text: str,
    user_prompt: str
) -> str:
    """
    Build a prompt with full HTML content but requesting unified diff output.

    For smaller HTML files, send the full content but still request
    unified diff output format instead of full HTML return.

    Args:
        html_content: Full HTML content
        citations_text: Formatted citations text
        user_prompt: User's modification instructions

    Returns:
        Prompt string
    """
    reader = HTMLReader(html_content)
    segments = reader.read_all_segments()

    # Combine all segments
    all_content = "\n".join(seg["content"] for seg in segments)

    prompt = f"""你是一个专业的UI/UX专家和前端开发者。请根据用户选择的HTML元素引用和修改指示，对提供的网页HTML代码进行精确修改。

## 用户选择的HTML元素引用

用户在网页中选择了以下元素作为修改的参考点：

{citations_text}

## 用户的修改指示

{user_prompt}

## HTML源代码（带行号）

```
{all_content}
```

(End of file - total {reader.total_lines} lines)

## 修改要求

1. **精确定位**：根据用户提供的选择器和HTML片段，以及行号标注，准确定位需要修改的元素
2. **使用 unified diff 格式输出修改**：不要返回完整HTML，而是只返回修改部分的 unified diff
3. **保留功能**：尽量保留原有的交互功能和样式
4. **最小化修改**：只修改必要的部分，不要改动无关代码

## 输出格式要求

请以 unified diff 格式输出你的修改。每个修改块使用以下格式：

```diff
--- original
+++ modified
@@ -起始行号,行数 +起始行号,行数 @@
 上下文行（不变的行）
-被删除的行
+新增的行
 上下文行（不变的行）
```

注意事项：
- 每个修改块至少包含3行上下文（不变的行）
- 行号必须与上方HTML源代码中的行号对应
- 可以包含多个 @@ 修改块
- 不要输出任何修改之外的解释文字

请直接输出 unified diff 内容，以 ```diff 开头，以 ``` 结尾。"""

    return prompt
