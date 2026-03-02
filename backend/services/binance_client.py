from __future__ import annotations

import time
import httpx
from typing import Any, Optional

FAPI_BASE = "https://fapi.binance.com"

# Simple in-memory cache: key -> (data, expire_at)
_cache: dict[str, tuple[Any, float]] = {}
CACHE_TTL = 1800  # 30 minutes


def _cache_get(key: str) -> Optional[Any]:
    entry = _cache.get(key)
    if entry and time.time() < entry[1]:
        return entry[0]
    return None


def _cache_set(key: str, data: Any) -> None:
    _cache[key] = (data, time.time() + CACHE_TTL)


async def get(path: str, params: Optional[dict] = None) -> Any:
    cache_key = path + str(sorted((params or {}).items()))
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{FAPI_BASE}{path}", params=params)
        resp.raise_for_status()
        data = resp.json()

    _cache_set(cache_key, data)
    return data


async def get_exchange_info() -> dict:
    return await get("/fapi/v1/exchangeInfo")


async def get_funding_info() -> list[dict]:
    return await get("/fapi/v1/fundingInfo")


async def get_funding_rate_history(symbol: str, limit: int = 2200) -> list[dict]:
    """Fetch funding rate records for `symbol` covering the past 2 years.

    Pages forward in time from 2 years ago to now (startTime → endTime),
    collecting up to `limit` records. This avoids Binance's 200-record cap
    that applies when endTime is omitted.
    """
    cache_key = f"funding_{symbol}_{limit}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    TWO_YEARS_MS = int(2 * 365 * 24 * 3600 * 1000)
    start_time_ms = int(time.time() * 1000) - TWO_YEARS_MS

    all_records: list[dict] = []
    current_start = start_time_ms

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            req_params: dict[str, Any] = {
                "symbol": symbol,
                "limit": 1000,
                "startTime": current_start,
            }

            resp = await client.get(f"{FAPI_BASE}/fapi/v1/fundingRate", params=req_params)
            resp.raise_for_status()
            batch: list[dict] = resp.json()

            if not batch:
                break

            all_records.extend(batch)

            if len(batch) < 1000:
                # reached the end of available data
                break

            # Advance start to just after the last record in this batch
            current_start = batch[-1]["fundingTime"] + 1

    # Keep only the most recent `limit` records
    all_records = all_records[-limit:]

    _cache_set(cache_key, all_records)
    return all_records


async def get_daily_klines(symbol: str, limit: int = 730) -> list[list]:
    """Fetch daily OHLCV klines."""
    return await get("/fapi/v1/klines", params={"symbol": symbol, "interval": "1d", "limit": limit})
