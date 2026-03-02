from __future__ import annotations

from datetime import datetime, timezone
from services import binance_client
from services.funding_service import get_interval_hours_map, normalize_to_8h, DEFAULT_INTERVAL_HOURS, _infer_interval_hours


def _day_start_ms(ts_ms: int) -> int:
    """Return the UTC midnight timestamp (ms) for the day that contains ts_ms."""
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(midnight.timestamp() * 1000)


def _fmt_time(ts_ms: int) -> str:
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d")


async def get_top5_price_surge_funding(symbol: str) -> list[dict]:
    """
    Find the 5 days with the highest 24h price increase for `symbol`,
    then return the 8h-normalized funding rate recorded on each of those days.

    Uses only the date range covered by the available funding rate records
    to ensure klines and funding data align.
    """
    interval_map = await get_interval_hours_map()
    interval_hours = interval_map.get(symbol, DEFAULT_INTERVAL_HOURS)

    klines, funding_records = await _fetch_both(symbol, interval_hours)

    # Determine funding data date range
    if funding_records:
        funding_start_ms = min(r["fundingTime"] for r in funding_records)
    else:
        funding_start_ms = 0

    # Build daily price change list — only within funding data coverage
    daily: list[dict] = []
    for k in klines:
        open_price = float(k[1])
        close_price = float(k[4])
        open_time_ms = int(k[0])
        if open_price == 0:
            continue
        if open_time_ms < funding_start_ms:
            continue
        change_pct = (close_price - open_price) / open_price * 100
        daily.append({"date": _fmt_time(open_time_ms), "openTimeMs": open_time_ms, "changePct": change_pct})

    daily.sort(key=lambda x: x["changePct"], reverse=True)
    top5_days = daily[:5]

    # 각 레코드에 당시 interval 사전 계산
    for i, r in enumerate(funding_records):
        r["_interval"] = interval_hours if i == 0 else _infer_interval_hours(funding_records[i - 1]["fundingTime"], r["fundingTime"])

    # Build a funding rate lookup keyed by day (UTC midnight ms)
    funding_by_day: dict[int, list[dict]] = {}
    for r in funding_records:
        day_key = _day_start_ms(r["fundingTime"])
        funding_by_day.setdefault(day_key, []).append(r)

    result = []
    for day in top5_days:
        day_key = _day_start_ms(day["openTimeMs"])
        day_records = funding_by_day.get(day_key, [])

        if day_records:
            def _safe_rate(r: dict) -> float:
                try:
                    return float(r.get("fundingRate", "") or "0")
                except (ValueError, TypeError):
                    return 0.0

            best = max(day_records, key=_safe_rate)
            raw_rate = _safe_rate(best)
            normalized = normalize_to_8h(raw_rate, best["_interval"])
            funding_time = best["fundingTime"]
            rec_interval = best["_interval"]
        else:
            raw_rate = 0.0
            normalized = 0.0
            funding_time = day["openTimeMs"]
            rec_interval = interval_hours

        result.append(
            {
                "date": day["date"],
                "changePct": round(day["changePct"], 4),
                "fundingTime": funding_time,
                "rawRate": round(raw_rate * 100, 6),
                "normalizedRate8h": round(normalized * 100, 6),
                "intervalHours": rec_interval,
            }
        )

    return result


async def _fetch_both(symbol: str, interval_hours: int = 8):
    """Fetch klines and funding history concurrently.
    Fetch 1000 funding records (the maximum reliably paginatable batch)
    and 500 daily candles; price range is filtered to funding coverage inside the caller.
    """
    import asyncio
    funding_limit = 730 * (24 // interval_hours)
    return await asyncio.gather(
        binance_client.get_daily_klines(symbol, limit=730),
        binance_client.get_funding_rate_history(symbol, limit=funding_limit),
    )
