import hashlib
import re
import time
import unicodedata
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import asyncio


@dataclass
class CacheEntry:
    """Cache entry with metadata"""

    answer: str
    question: str
    context_count: int  # Number of chunks
    timestamp: float
    hit_count: int = 0  # Number of times this cache got accessed


class RAGCacheManager:
    """Thread-safe cache manager for RAG responses"""

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        """
        Args:
            ttl_seconds: Time to live for cache entries (default 1 hour)
            max_size: The max number of entries in cache
        """
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    def _generate_key(self, question: str) -> str:
        # Normalize unicode
        normalized = unicodedata.normalize("NFKC", question)
        # Lowercase
        normalized = normalized.lower()
        # Remove extra whitespace
        normalized = re.sub(r"\s+", " ", normalized).strip()
        # Remove punctuation variations
        normalized = re.sub(r"[?.!,;]+", "", normalized)

        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if a entry is expired"""
        return time.time() - entry.timestamp > self.ttl_seconds

    async def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key
            for key, entry in self._cache.items()
            if current_time - entry.timestamp > self.ttl_seconds
        ]
        for key in expired_keys:
            del self._cache[key]

    async def _evict_lru(self):
        """Evict least recently used entries if cache is full"""
        if len(self._cache) >= self.max_size:
            lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].hit_count)
            del self._cache[lru_key]

    async def get(self, question: str) -> Optional[Tuple[str, str, int]]:
        """
        Get cached answer for question

        Returns:
            Tuple of (answer, question, context_count) or None if not found/expired
        """
        key = self._generate_key(question)

        async with self._lock:
            await self._cleanup_expired()

            if key not in self._cache:
                return None

            entry = self._cache[key]
            if self._is_expired(entry):
                del self._cache[key]
                return None

            # Update hit count
            entry.hit_count += 1

            return (entry.answer, entry.question, entry.context_count)

    async def set(self, question: str, answer: str, context_count: int):
        """Cache answer for question"""
        key = self._generate_key(question)

        async with self._lock:
            await self._cleanup_expired()
            await self._evict_lru()

            self._cache[key] = CacheEntry(
                answer=answer,
                question=question,
                context_count=context_count,
                timestamp=time.time(),
                hit_count=0,
            )

    async def clear(self):
        """Clear all cache"""
        async with self._lock:
            self._cache.clear()

    async def get_stats(self) -> Dict:
        """Get cache statistics"""
        async with self._lock:
            await self._cleanup_expired()
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "entries": [
                    {
                        "question": (
                            entry.question[:50] + "..."
                            if len(entry.question) > 50
                            else entry.question
                        ),
                        "hit_count": entry.hit_count,
                        "age_seconds": time.time() - entry.timestamp,
                    }
                    for entry in self._cache.values()
                ],
            }


_cache_manager: Optional[RAGCacheManager] = None


async def get_cache_manager(
    ttl_seconds: int = 3600, max_size: int = 1000
) -> RAGCacheManager:
    """Get singleton cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = RAGCacheManager(ttl_seconds, max_size)
    return _cache_manager
