"""
In-memory cache with TTL support for frequently accessed Bible verses.
"""
import time
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class VerseCache:
    """Simple in-memory cache with time-to-live expiration."""

    def __init__(self, default_ttl: int = 3600):
        self._store: dict[str, dict] = {}
        self._default_ttl = default_ttl  # seconds

    # ── public API ──────────────────────────────────────────────

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.time() > entry["expires"]:
            del self._store[key]
            return None
        logger.debug("Cache HIT  → %s", key)
        return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._store[key] = {
            "value": value,
            "expires": time.time() + (ttl or self._default_ttl),
        }
        logger.debug("Cache SET  → %s (ttl=%s)", key, ttl or self._default_ttl)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    @property
    def size(self) -> int:
        return len(self._store)

    # ── helpers ─────────────────────────────────────────────────

    @staticmethod
    def make_key(*parts: str) -> str:
        """Build a normalised cache key from variable parts."""
        return ":".join(str(p).strip().lower() for p in parts)


# ── singleton instance ──────────────────────────────────────────
verse_cache = VerseCache(default_ttl=3600)   # 1-hour TTL
