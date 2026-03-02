from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from services import binance_client

# Default funding interval when fundingInfo doesn't include a symbol
DEFAULT_INTERVAL_HOURS = 4


async def get_interval_hours_map() -> dict[str, int]:
    """Return a mapping of symbol -> fundingIntervalHours.
    Symbols not listed in fundingInfo default to 8h."""
    info_list = await binance_client.get_funding_info()
    return {item["symbol"]: item["fundingIntervalHours"] for item in info_list}


def normalize_to_8h(rate: float, interval_hours: int) -> float:
    """Scale a funding rate to 8h equivalent."""
    return rate * (8 / interval_hours)


def _infer_interval_hours(prev_ts_ms: int, curr_ts_ms: int) -> int:
    """두 연속 fundingTime 차이(ms)로 당시 interval_hours를 역산."""
    diff_hours = round((curr_ts_ms - prev_ts_ms) / (1000 * 3600))
    for valid in (1, 2, 4, 8):
        if diff_hours <= valid:
            return valid
    return 8


KST = timezone(timedelta(hours=9))

def _fmt_time(ts_ms: int) -> str:
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).astimezone(KST)
    return dt.strftime("%Y-%m-%d %H:%M")


def _day_start_ms(ts_ms: int) -> int:
    """Return the UTC midnight timestamp (ms) for the day that contains ts_ms."""
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(midnight.timestamp() * 1000)


async def get_top5_funding_rates(symbol: str) -> list[dict]:
    """Return the 5 lowest 8h-normalized funding rate records for `symbol`."""
    interval_map = await get_interval_hours_map()
    interval_hours = interval_map.get(symbol, DEFAULT_INTERVAL_HOURS)

    funding_limit = 730 * (24 // interval_hours)
    klines, records = await asyncio.gather(
        binance_client.get_daily_klines(symbol, limit=730),
        binance_client.get_funding_rate_history(symbol, limit=funding_limit),
    )

    # Build day -> changePct map from klines
    change_pct_by_day: dict[int, float] = {}
    for k in klines:
        open_time_ms = int(k[0])
        open_price = float(k[1])
        close_price = float(k[4])
        if open_price == 0:
            continue
        change_pct = (close_price - open_price) / open_price * 100
        change_pct_by_day[open_time_ms] = change_pct

    enriched = []
    for i, r in enumerate(records):
        rec_interval = interval_hours if i == 0 else _infer_interval_hours(records[i - 1]["fundingTime"], r["fundingTime"])
        rate_str = r.get("fundingRate", "") or "0"
        mark_str = r.get("markPrice", "") or "0"
        try:
            raw_rate = float(rate_str)
        except (ValueError, TypeError):
            continue
        normalized = normalize_to_8h(raw_rate, rec_interval)
        try:
            mark_price = float(mark_str)
        except (ValueError, TypeError):
            mark_price = 0.0
        day_key = _day_start_ms(r["fundingTime"])
        change_pct = change_pct_by_day.get(day_key)
        enriched.append(
            {
                "time": _fmt_time(r["fundingTime"]),
                "timestamp": r["fundingTime"],
                "rawRate": raw_rate * 100,
                "normalizedRate8h": normalized * 100,
                "markPrice": mark_price,
                "intervalHours": rec_interval,
                "changePct": round(change_pct, 4) if change_pct is not None else None,
            }
        )

    # Sort ascending by normalized rate and return bottom 5 (lowest)
    enriched.sort(key=lambda x: x["normalizedRate8h"], reverse=False)
    return enriched[:5]
