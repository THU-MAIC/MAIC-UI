"""
Cache System Module

This module provides caching functionality for Heavy Mode generation.
Successful generations are cached to serve as fallbacks for future failures.

Date: 2025-01-15
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import time

logger = logging.getLogger(__name__)


class GenerationCache:
    """Cache for storing successful HTML generations."""

    def __init__(self, cache_dir: str = "cache"):
        """
        Initialize the cache system.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        logger.info(f"Cache initialized at {self.cache_dir}")

    def _get_content_hash(self, content: Dict) -> str:
        """
        Generate hash for content identification.

        Args:
            content: Content dict to hash

        Returns:
            Hex digest hash string
        """
        # Create deterministic string representation
        content_str = json.dumps(content, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(content_str.encode()).hexdigest()

    def _get_cache_path(self, content_hash: str, stage: str) -> Path:
        """
        Get cache file path for a content hash and stage.

        Args:
            content_hash: Hash of the content
            stage: Generation stage (stage1, stage2, stage3, stage4)

        Returns:
            Path object for cache file
        """
        return self.cache_dir / f"{content_hash}_{stage}.html"

    def save_success(self, content: Dict, stage: str, html: str) -> bool:
        """
        Save successful generation to cache.

        Args:
            content: Content dict that was used for generation
            stage: Generation stage
            html: Generated HTML to cache

        Returns:
            True if saved successfully
        """
        try:
            content_hash = self._get_content_hash(content)
            cache_path = self._get_cache_path(content_hash, stage)

            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(html)

            logger.info(f"Cached {stage} for hash {content_hash[:8]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to cache {stage}: {e}")
            return False

    def get_cached(self, content: Dict, stage: str) -> Optional[str]:
        """
        Retrieve cached HTML if available.

        Args:
            content: Content dict to look up
            stage: Generation stage to retrieve

        Returns:
            Cached HTML string or None
        """
        try:
            content_hash = self._get_content_hash(content)
            cache_path = self._get_cache_path(content_hash, stage)

            if cache_path.exists():
                with open(cache_path, 'r', encoding='utf-8') as f:
                    html = f.read()
                logger.info(f"Cache hit for {stage} with hash {content_hash[:8]}...")
                return html

            logger.debug(f"Cache miss for {stage} with hash {content_hash[:8]}...")
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve cache for {stage}: {e}")
            return None

    def save_metadata(self, content: Dict, metadata: Dict[str, Any]) -> bool:
        """
        Save generation metadata.

        Args:
            content: Content dict
            metadata: Metadata to save

        Returns:
            True if saved successfully
        """
        try:
            content_hash = self._get_content_hash(content)
            metadata_path = self.cache_dir / f"{content_hash}_metadata.json"

            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            return False

    def get_metadata(self, content: Dict) -> Optional[Dict]:
        """
        Retrieve cached metadata.

        Args:
            content: Content dict to look up

        Returns:
            Metadata dict or None
        """
        try:
            content_hash = self._get_content_hash(content)
            metadata_path = self.cache_dir / f"{content_hash}_metadata.json"

            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)

            return None

        except Exception as e:
            logger.error(f"Failed to retrieve metadata: {e}")
            return None

    def clear_old_cache(self, max_age_hours: int = 24):
        """
        Clear cache entries older than specified age.

        Args:
            max_age_hours: Maximum age in hours
        """
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            removed_count = 0

            for cache_file in self.cache_dir.glob("*"):
                if cache_file.is_file():
                    file_age = current_time - cache_file.stat().st_mtime
                    if file_age > max_age_seconds:
                        cache_file.unlink()
                        removed_count += 1

            logger.info(f"Cleared {removed_count} old cache files")

        except Exception as e:
            logger.error(f"Failed to clear old cache: {e}")

    def clear_all_cache(self):
        """Clear all cache files."""
        try:
            removed_count = 0
            for cache_file in self.cache_dir.glob("*"):
                if cache_file.is_file():
                    cache_file.unlink()
                    removed_count += 1

            logger.info(f"Cleared all {removed_count} cache files")

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about cache usage.

        Returns:
            Dict with cache statistics
        """
        try:
            cache_files = list(self.cache_dir.glob("*"))
            total_size = sum(f.stat().st_size for f in cache_files if f.is_file())

            # Count by stage
            stage_counts = {}
            for f in cache_files:
                if f.is_file() and f.suffix == '.html':
                    stage = f.stem.split('_')[-1]
                    stage_counts[stage] = stage_counts.get(stage, 0) + 1

            return {
                "total_files": len(cache_files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "stage_counts": stage_counts,
                "cache_dir": str(self.cache_dir)
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}


# Global cache instance
_cache_instance = None


def get_cache(cache_dir: str = "cache") -> GenerationCache:
    """
    Get or create the global cache instance.

    Args:
        cache_dir: Directory for cache storage

    Returns:
        GenerationCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = GenerationCache(cache_dir)
    return _cache_instance
