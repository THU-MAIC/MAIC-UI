"""
HTML Modifier - Apply unified diff patches to HTML content.

Inspired by opencode's agent.ts, this module provides:
- Unified diff parsing from AI responses
- Patch application to original HTML
- Validation and error handling for diff operations

This allows AI models to output minimal diffs instead of full HTML,
reducing response size and improving precision.
"""

from typing import Dict, List, Optional, Tuple
import difflib
import re
import logging

logger = logging.getLogger(__name__)


class DiffParseError(Exception):
    """Error parsing unified diff."""
    pass


class DiffApplyError(Exception):
    """Error applying unified diff to content."""
    pass


class UnifiedDiffParser:
    """
    Parser for unified diff format.

    Handles standard unified diff format:
    --- original
    +++ modified
    @@ -start,count +start,count @@
     context line
    -removed line
    +added line
    """

    # Regex patterns for diff parsing
    HUNK_HEADER_PATTERN = re.compile(
        r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@'
    )

    @classmethod
    def extract_diff_from_response(cls, response: str) -> Optional[str]:
        """
        Extract unified diff content from AI response.

        Looks for content between ```diff and ``` markers.

        Args:
            response: Raw AI response text

        Returns:
            Extracted diff content or None if not found
        """
        # Try to find diff block with markers
        diff_pattern = re.compile(
            r'```diff\s*\n(.*?)```',
            re.DOTALL
        )
        match = diff_pattern.search(response)

        if match:
            return match.group(1).strip()

        # Try without language specifier
        generic_pattern = re.compile(
            r'```\s*\n(---.*?)```',
            re.DOTALL
        )
        match = generic_pattern.search(response)

        if match:
            return match.group(1).strip()

        # Check if the entire response looks like a diff
        if response.strip().startswith('---') or response.strip().startswith('@@'):
            return response.strip()

        return None

    @classmethod
    def parse_hunks(cls, diff_content: str) -> List[Dict]:
        """
        Parse unified diff into individual hunks.

        Args:
            diff_content: Unified diff text

        Returns:
            List of hunk dictionaries with:
                - old_start: Starting line in original
                - old_count: Number of lines in original
                - new_start: Starting line in modified
                - new_count: Number of lines in modified
                - lines: List of (operation, content) tuples
                    - operation: ' ' (context), '-' (remove), '+' (add)
        """
        hunks = []
        lines = diff_content.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i]

            # Skip file headers
            if line.startswith('---') or line.startswith('+++'):
                i += 1
                continue

            # Parse hunk header
            match = cls.HUNK_HEADER_PATTERN.match(line)
            if match:
                old_start = int(match.group(1))
                old_count = int(match.group(2)) if match.group(2) else 1
                new_start = int(match.group(3))
                new_count = int(match.group(4)) if match.group(4) else 1

                hunk = {
                    'old_start': old_start,
                    'old_count': old_count,
                    'new_start': new_start,
                    'new_count': new_count,
                    'lines': []
                }

                i += 1

                # Collect hunk lines until next hunk or end
                while i < len(lines):
                    hunk_line = lines[i]

                    # Check if this is a new hunk header
                    if cls.HUNK_HEADER_PATTERN.match(hunk_line):
                        break

                    # Skip file headers that might appear mid-diff
                    if hunk_line.startswith('---') or hunk_line.startswith('+++'):
                        i += 1
                        continue

                    # Skip empty lines at end of diff
                    if not hunk_line and i == len(lines) - 1:
                        break

                    # Parse line operation
                    if hunk_line.startswith('-') and not hunk_line.startswith('---'):
                        hunk['lines'].append(('-', hunk_line[1:]))
                    elif hunk_line.startswith('+') and not hunk_line.startswith('+++'):
                        hunk['lines'].append(('+', hunk_line[1:]))
                    elif hunk_line.startswith(' '):
                        # Context line with space prefix
                        hunk['lines'].append((' ', hunk_line[1:]))
                    elif hunk_line == '':
                        # Empty line in context
                        hunk['lines'].append((' ', ''))
                    elif hunk_line.startswith('\\'):
                        # "\ No newline at end of file" - skip
                        i += 1
                        continue
                    else:
                        # No prefix - treat as context line (some diffs omit the space)
                        # Log a warning as this might indicate parsing issues
                        logger.debug(f"Line without standard prefix at position {i}: {hunk_line[:50]!r}")
                        hunk['lines'].append((' ', hunk_line))

                    i += 1

                if hunk['lines']:  # Only add hunk if it has content
                    hunks.append(hunk)
                    logger.debug(f"Parsed hunk: {len(hunk['lines'])} lines at position {hunk['old_start']}")
            else:
                i += 1

        return hunks


class HTMLModifier:
    """
    Apply unified diffs to HTML content.

    Handles line-numbered HTML content and applies patches
    precisely based on line numbers from the diff.
    """

    def __init__(self, original_content: str):
        """
        Initialize with original HTML content.

        Args:
            original_content: Original HTML string
        """
        self._original = original_content
        self._lines = original_content.splitlines(keepends=True)
        # Ensure all lines have newline except possibly the last
        self._lines = [
            line if line.endswith('\n') else line + '\n'
            for line in self._lines[:-1]
        ] + ([self._lines[-1]] if self._lines else [])

        self._total_lines = len(self._lines)
        logger.info(f"HTMLModifier initialized: {self._total_lines} lines")

        # Precompile a regex to strip HTML attributes for fuzzy matching
        self._attr_strip_pattern = re.compile(r"<([a-zA-Z0-9]+)(\s+[^>]+)>")

    @property
    def total_lines(self) -> int:
        """Total number of lines in original content."""
        return self._total_lines

    def _normalize_line_for_match(self, line: str) -> str:
        """Normalize a line for lenient comparison (trim, collapse attrs)."""
        base = line.rstrip('\n\r').strip()
        # Remove attributes inside tags to tolerate style/class drift while keeping tag names
        base = self._attr_strip_pattern.sub(r"<\1>", base)
        return base

    def _validate_html_structure(self, html: str) -> Dict:
        """
        Basic validation of HTML structure after modification.

        Args:
            html: Modified HTML content

        Returns:
            Dict with 'valid' bool and optional 'warning' message
        """
        warnings = []

        # Check for basic HTML structure
        html_lower = html.lower()
        if '<html' not in html_lower:
            warnings.append("Missing <html> tag")
        if '</html>' not in html_lower:
            warnings.append("Missing </html> closing tag")
        if '<body' not in html_lower:
            warnings.append("Missing <body> tag")
        if '</body>' not in html_lower:
            warnings.append("Missing </body> closing tag")

        # Check for common broken patterns
        if '<<' in html or '>>' in html:
            warnings.append("Detected double angle brackets (possible malformed tags)")

        # Check tag balance for common tags
        for tag in ['div', 'span', 'p', 'section', 'article']:
            open_count = html_lower.count(f'<{tag}') - html_lower.count(f'<{tag}/')
            close_count = html_lower.count(f'</{tag}>')
            if abs(open_count - close_count) > 2:
                warnings.append(f"Unbalanced <{tag}> tags (open: {open_count}, close: {close_count})")

        if warnings:
            return {"valid": False, "warning": "; ".join(warnings)}
        return {"valid": True}

    def apply_diff(self, diff_content: str) -> Dict:
        """
        Apply unified diff to the HTML content.

        Args:
            diff_content: Unified diff text

        Returns:
            Dict with:
                - status: "success" or "error"
                - modified_html: Modified HTML content
                - hunks_applied: Number of hunks successfully applied
                - error: Error message if status is "error"
        """
        try:
            hunks = UnifiedDiffParser.parse_hunks(diff_content)

            if not hunks:
                logger.warning("No valid hunks found in diff")
                return {
                    "status": "error",
                    "error": "No valid hunks found in diff",
                    "modified_html": self._original,
                    "hunks_applied": 0
                }

            logger.info(f"Applying {len(hunks)} hunk(s) to HTML")

            # Apply hunks in reverse order to maintain line numbers
            modified_lines = list(self._lines)
            hunks_applied = 0

            # Sort hunks by old_start in descending order
            sorted_hunks = sorted(hunks, key=lambda h: h['old_start'], reverse=True)

            for hunk in sorted_hunks:
                try:
                    modified_lines = self._apply_hunk(modified_lines, hunk)
                    hunks_applied += 1
                    logger.debug(f"Applied hunk at line {hunk['old_start']}")
                except DiffApplyError as e:
                    logger.warning(f"Failed to apply hunk at line {hunk['old_start']}: {e}")
                    # Continue with other hunks

            modified_html = ''.join(modified_lines)

            # Clean up trailing newlines if original didn't have one
            if not self._original.endswith('\n') and modified_html.endswith('\n'):
                modified_html = modified_html.rstrip('\n')

            # Validate the modified HTML has proper structure
            validation_result = self._validate_html_structure(modified_html)
            if not validation_result["valid"]:
                logger.warning(f"HTML validation warning: {validation_result['warning']}")

            logger.info(f"Successfully applied {hunks_applied}/{len(hunks)} hunks")

            return {
                "status": "success",
                "modified_html": modified_html,
                "hunks_applied": hunks_applied,
                "total_hunks": len(hunks)
            }

        except Exception as e:
            logger.error(f"Error applying diff: {e}")
            return {
                "status": "error",
                "error": str(e),
                "modified_html": self._original,
                "hunks_applied": 0
            }

    def _apply_hunk(self, lines: List[str], hunk: Dict) -> List[str]:
        """
        Apply a single hunk to the lines.

        Args:
            lines: Current lines of the file
            hunk: Hunk dictionary from parser

        Returns:
            Modified lines list
        """
        old_start = hunk['old_start'] - 1  # Convert to 0-indexed

        # Validate start position
        if old_start < 0 or old_start > len(lines):
            raise DiffApplyError(f"Hunk start line {hunk['old_start']} out of range")

        # Build expected and replacement lines
        expected_lines = []
        replacement_lines = []

        for op, content in hunk['lines']:
            if op == ' ':
                # Context line - should be in both
                expected_lines.append(content + '\n' if not content.endswith('\n') else content)
                replacement_lines.append(content + '\n' if not content.endswith('\n') else content)
            elif op == '-':
                # Removed line - only in expected
                expected_lines.append(content + '\n' if not content.endswith('\n') else content)
            elif op == '+':
                # Added line - only in replacement
                replacement_lines.append(content + '\n' if not content.endswith('\n') else content)

        # Log expected vs actual context for debugging
        logger.debug(f"Applying hunk at line {hunk['old_start']}, expecting {len(expected_lines)} lines")
        if expected_lines and old_start < len(lines):
            logger.debug(f"Expected first line: {expected_lines[0][:80]!r}")
            logger.debug(f"Actual first line:   {lines[old_start][:80]!r}")

        # Verify context matches (with strict matching for HTML)
        if not self._verify_context(lines, old_start, expected_lines, tolerance=0.95):
            # Try fuzzy search around the expected location
            found_start = self._fuzzy_find_context(lines, old_start, expected_lines)
            if found_start is not None:
                logger.info(f"Fuzzy matched hunk at line {found_start + 1} (expected {hunk['old_start']})")
                old_start = found_start
            else:
                # Log more details about the mismatch
                if expected_lines and old_start < len(lines):
                    logger.error(f"Context mismatch details:")
                    for i, exp in enumerate(expected_lines[:3]):
                        if old_start + i < len(lines):
                            logger.error(f"  Line {old_start + i + 1}: expected {exp[:60]!r}")
                            logger.error(f"  Line {old_start + i + 1}: actual   {lines[old_start + i][:60]!r}")

                # Last-resort: scan entire file for the best matching window
                best_index, best_score = self._best_effort_context_search(lines, expected_lines)
                if best_index is not None and best_score >= 0.5:
                    logger.warning(
                        "Best-effort matched hunk at line %d (score %.2f%%, expected %d)",
                        best_index + 1,
                        best_score * 100,
                        hunk['old_start']
                    )
                    old_start = best_index
                else:
                    raise DiffApplyError(
                        f"Context mismatch at line {hunk['old_start']}. "
                        "The original content may have changed."
                    )

        # Apply the replacement
        result = lines[:old_start] + replacement_lines + lines[old_start + len(expected_lines):]

        return result

    def _verify_context(
        self,
        lines: List[str],
        start: int,
        expected: List[str],
        tolerance: float = 0.85
    ) -> bool:
        """
        Verify that expected lines match actual lines at position.

        Args:
            lines: File lines
            start: Starting index
            expected: Expected lines to match
            tolerance: Minimum ratio of matching lines (0-1)

        Returns:
            True if context matches within tolerance
        """
        if start + len(expected) > len(lines):
            return False

        if not expected:
            return True

        matches = 0
        for i, exp_line in enumerate(expected):
            actual = lines[start + i]
            # Normalize for comparison - strip whitespace and HTML attributes for robust matching
            exp_normalized = self._normalize_line_for_match(exp_line)
            actual_normalized = self._normalize_line_for_match(actual)

            if exp_normalized == actual_normalized:
                matches += 1
            elif exp_normalized in actual_normalized or actual_normalized in exp_normalized:
                # Partial match - count as half
                matches += 0.5

        ratio = matches / len(expected)
        logger.debug(f"Context verification at line {start + 1}: {matches}/{len(expected)} matches ({ratio:.2%})")
        return ratio >= tolerance

    def _fuzzy_find_context(
        self,
        lines: List[str],
        expected_start: int,
        expected_lines: List[str],
        search_range: int = 20
    ) -> Optional[int]:
        """
        Fuzzy search for context around expected location.

        Args:
            lines: File lines
            expected_start: Expected starting index
            expected_lines: Lines to match
            search_range: Number of lines to search around expected

        Returns:
            Found starting index or None
        """
        if not expected_lines:
            return expected_start

        best_match = None
        best_score = 0.0

        # Search in expanding range around expected position
        for offset in range(search_range):
            for direction in [1, -1]:
                check_start = expected_start + (offset * direction)

                if check_start < 0 or check_start + len(expected_lines) > len(lines):
                    continue

                # Calculate match score
                score = self._calculate_match_score(lines, check_start, expected_lines)
                if score > best_score and score >= 0.85:
                    best_score = score
                    best_match = check_start

        if best_match is not None:
            logger.info(f"Fuzzy matched with score {best_score:.2%} at line {best_match + 1}")

        return best_match

    def _best_effort_context_search(
        self,
        lines: List[str],
        expected_lines: List[str]
    ) -> Tuple[Optional[int], float]:
        """Find the best matching window in the entire file when local context fails."""
        if not expected_lines or len(lines) < len(expected_lines):
            return None, 0.0

        normalized_expected = [self._normalize_line_for_match(l) for l in expected_lines]
        window = len(normalized_expected)
        best_index: Optional[int] = None
        best_score = 0.0

        for start in range(0, len(lines) - window + 1):
            candidate = [self._normalize_line_for_match(lines[start + i]) for i in range(window)]
            score = difflib.SequenceMatcher(None, normalized_expected, candidate).ratio()

            if score > best_score:
                best_score = score
                best_index = start

        return best_index, best_score

    def _calculate_match_score(
        self,
        lines: List[str],
        start: int,
        expected: List[str]
    ) -> float:
        """Calculate exact match score for context verification."""
        if start + len(expected) > len(lines):
            return 0.0

        if not expected:
            return 1.0

        total_score = 0.0
        for i, exp_line in enumerate(expected):
            actual = lines[start + i]
            exp_normalized = self._normalize_line_for_match(exp_line)
            actual_normalized = self._normalize_line_for_match(actual)

            if exp_normalized == actual_normalized:
                total_score += 1.0
            elif exp_normalized and actual_normalized:
                # Calculate character-level similarity for partial matches
                shorter = min(len(exp_normalized), len(actual_normalized))
                longer = max(len(exp_normalized), len(actual_normalized))
                if longer > 0:
                    # Simple prefix/suffix matching
                    common = 0
                    for j in range(shorter):
                        if exp_normalized[j] == actual_normalized[j]:
                            common += 1
                        else:
                            break
                    total_score += common / longer * 0.5

        return total_score / len(expected)


def apply_unified_diff(original_html: str, diff_content: str) -> Dict:
    """
    Convenience function to apply unified diff to HTML.

    Args:
        original_html: Original HTML content
        diff_content: Unified diff text (may include ```diff markers)

    Returns:
        Dict with status, modified_html, and metadata
    """
    # Extract diff from response if wrapped in code block
    extracted_diff = UnifiedDiffParser.extract_diff_from_response(diff_content)

    if not extracted_diff:
        logger.warning("Could not extract diff from response")
        return {
            "status": "error",
            "error": "Could not extract valid unified diff from response",
            "modified_html": original_html,
            "hunks_applied": 0
        }

    logger.info("Extracted unified diff:\n%s", extracted_diff)

    modifier = HTMLModifier(original_html)
    return modifier.apply_diff(extracted_diff)


def get_new_content(file_original: str, unified_diff: str) -> str:
    """
    Apply unified diff and return new content (matches opencode's getNewContent).

    Args:
        file_original: Original file content
        unified_diff: Unified diff to apply

    Returns:
        Modified content string

    Raises:
        DiffApplyError: If diff cannot be applied
    """
    result = apply_unified_diff(file_original, unified_diff)

    if result["status"] == "error":
        raise DiffApplyError(result.get("error", "Unknown error applying diff"))

    return result["modified_html"]
