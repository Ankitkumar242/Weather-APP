"""Caching infrastructure with TTLCache, stale fallback, request coalescing, and debug stats."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import Any

from cachetools import TTLCache

from app.config import get_settings

settings = get_settings()


class CacheItem:
    """Wrapped cache item preserving value and creation timestamp."""

    def __init__(self, value: Any, fetched_at: datetime | None = None) -> None:
        self.value = value
        self.fetched_at = fetched_at or datetime.now(UTC)


class CacheManager:
    """Manages TTL caches, stale fallbacks, request coalescing, and debug metrics."""

    def __init__(self) -> None:
        self.forecast_cache: TTLCache[str, CacheItem] = TTLCache(
            maxsize=2000, ttl=settings.cache_ttl_forecast
        )
        self.air_quality_cache: TTLCache[str, CacheItem] = TTLCache(
            maxsize=2000, ttl=settings.cache_ttl_air_quality
        )
        self.state_overview_cache: TTLCache[str, CacheItem] = TTLCache(
            maxsize=200, ttl=settings.cache_ttl_state_overview
        )
        self.search_cache: TTLCache[str, CacheItem] = TTLCache(
            maxsize=1000, ttl=settings.cache_ttl_search
        )
        self.reverse_geo_cache: TTLCache[str, CacheItem] = TTLCache(
            maxsize=5000, ttl=settings.cache_ttl_reverse_geo
        )
        self.ip_locate_cache: TTLCache[str, CacheItem] = TTLCache(
            maxsize=2000, ttl=settings.cache_ttl_ip_locate
        )

        # Secondary persistent store for stale data fallback
        self._stale_store: dict[str, CacheItem] = {}

        # Request coalescing (single-flight) locks
        self._locks: dict[str, asyncio.Lock] = {}
        self._master_lock = asyncio.Lock()

        # Debug call & hit tracking
        self.total_cache_hits = 0
        self.total_upstream_calls = 0
        self.recent_upstream_logs: list[dict[str, Any]] = []

    def _get_cache(self, category: str) -> TTLCache[str, CacheItem] | None:
        caches = {
            "forecast": self.forecast_cache,
            "air_quality": self.air_quality_cache,
            "state_overview": self.state_overview_cache,
            "search": self.search_cache,
            "reverse_geo": self.reverse_geo_cache,
            "ip_locate": self.ip_locate_cache,
        }
        return caches.get(category)

    @staticmethod
    def coord_key(lat: float, lon: float) -> str:
        """Round coordinates to 2 decimal places for consistent cache keys."""
        return f"{round(lat, 2):.2f}:{round(lon, 2):.2f}"

    def get(self, category: str, key: str) -> tuple[Any | None, bool]:
        """
        Get value from cache.
        Returns: (value, is_stale)
        """
        cache = self._get_cache(category)
        full_key = f"{category}:{key}"

        if cache is not None and key in cache:
            self.total_cache_hits += 1
            item = cache[key]
            return item.value, False

        # If not in fresh cache, check stale store
        if full_key in self._stale_store:
            stale_item = self._stale_store[full_key]
            return stale_item.value, True

        return None, False

    def set(self, category: str, key: str, value: Any) -> None:
        """Set value in cache and save in stale fallback store."""
        cache = self._get_cache(category)
        full_key = f"{category}:{key}"
        item = CacheItem(value=value)

        if cache is not None:
            cache[key] = item

        # Also store in stale storage
        self._stale_store[full_key] = item

    async def get_or_set_coalesced(
        self,
        category: str,
        key: str,
        fetch_coro_fn: Callable[[], Coroutine[Any, Any, Any]],
    ) -> tuple[Any, bool]:
        """
        Single-flight coalescing:
        Checks fresh cache. If absent, locks on key so parallel calls wait for a single fetch.
        If fetch fails and stale fallback is available, returns stale fallback with is_stale=True.
        """
        # Quick check without lock
        val, is_stale = self.get(category, key)
        if val is not None and not is_stale:
            return val, False

        full_key = f"{category}:{key}"
        async with self._master_lock:
            if full_key not in self._locks:
                self._locks[full_key] = asyncio.Lock()
            lock = self._locks[full_key]

        async with lock:
            # Re-check cache after acquiring lock
            val, is_stale = self.get(category, key)
            if val is not None and not is_stale:
                return val, False

            # Need to fetch upstream
            try:
                result = await fetch_coro_fn()
                self.set(category, key, result)
                return result, False
            except Exception as e:
                # If upstream fails, check stale fallback
                stale_val, _ = self.get(category, key)
                if stale_val is not None:
                    return stale_val, True
                raise e

    def record_upstream_call(
        self, endpoint: str, params: dict[str, Any] | None, status_code: int, duration_ms: float
    ) -> None:
        """Record upstream call for ?debug=1 inspection."""
        self.total_upstream_calls += 1
        entry = {
            "endpoint": endpoint,
            "params": params,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.recent_upstream_logs.append(entry)
        if len(self.recent_upstream_logs) > 50:
            self.recent_upstream_logs.pop(0)

    def get_debug_stats(self) -> dict[str, Any]:
        """Return cache and upstream call metrics."""
        return {
            "total_cache_hits": self.total_cache_hits,
            "total_upstream_calls": self.total_upstream_calls,
            "recent_logs": self.recent_upstream_logs[-10:],
        }


# Global cache manager instance
cache_manager = CacheManager()
