"""Async HTTP client with connection pooling, retries, exponential backoff, and jitter."""

from __future__ import annotations

import asyncio
import random
import time
from typing import Any

import httpx

from app.config import get_settings
from app.core.cache import cache_manager

settings = get_settings()

_http_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Return active httpx.AsyncClient singleton."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.http_timeout_seconds),
            headers={"User-Agent": settings.nominatim_user_agent},
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
        )
    return _http_client


async def close_http_client() -> None:
    """Close the global client session."""
    global _http_client
    if _http_client is not None and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None


async def resilient_request(
    method: str,
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    max_retries: int | None = None,
) -> httpx.Response:
    """
    Execute HTTP request with retries, exponential backoff, and jitter.
    Logs upstream calls to cache_manager for ?debug=1.
    """
    client = get_http_client()
    retries = max_retries if max_retries is not None else settings.http_max_retries
    attempt = 0

    last_exc: Exception | None = None

    while attempt <= retries:
        req_start = time.perf_counter()
        try:
            response = await client.request(method, url, params=params, headers=headers)
            elapsed_ms = (time.perf_counter() - req_start) * 1000
            cache_manager.record_upstream_call(
                endpoint=url,
                params=params,
                status_code=response.status_code,
                duration_ms=elapsed_ms,
            )

            # Retry on 5xx server errors or 429 Too Many Requests
            if response.status_code >= 500 or response.status_code == 429:
                if attempt < retries:
                    attempt += 1
                    backoff = (
                        settings.http_backoff_factor * (2 ** (attempt - 1))
                    ) + random.uniform(0, 0.2)
                    await asyncio.sleep(backoff)
                    continue
                response.raise_for_status()

            return response

        except (httpx.RequestError, httpx.TimeoutException) as exc:
            elapsed_ms = (time.perf_counter() - req_start) * 1000
            cache_manager.record_upstream_call(
                endpoint=url, params=params, status_code=0, duration_ms=elapsed_ms
            )
            last_exc = exc
            if attempt < retries:
                attempt += 1
                backoff = (settings.http_backoff_factor * (2 ** (attempt - 1))) + random.uniform(
                    0, 0.2
                )
                await asyncio.sleep(backoff)
                continue
            raise exc

    if last_exc:
        raise last_exc
    raise RuntimeError("Unexpected end of resilient_request loop")
