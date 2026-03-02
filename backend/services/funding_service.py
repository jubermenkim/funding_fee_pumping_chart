from __future__ import annotations

import asyncio
import time
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


def _hour_start_ms(ts_ms: int) -> int:
    """Return the UTC hour-start timestamp (ms) for the hour that contains ts_ms."""
    return (ts_ms // (3600 * 1000)) * (3600 * 1000)


def _get_change_pct(funding_time_ms: int, mark_price: float, close_price_by_hour: dict[int, float]) -> float | None:
    """펀딩피 시각 기준 직전 24시간 상승률 계산.

    mark_price: 펀딩피 시각의 가격 (현재)
    close_price_by_hour: 시간봉 close price lookup (open_time_ms -> close_price)
    24시간 전 가격: funding_time_ms - 24h 에 해당하는 시간봉의 close price
    """
    if not mark_price:
        return None
    ms_24h = 24 * 3600 * 1000
    hour_start_24h_ago = _hour_start_ms(funding_time_ms - ms_24h)
    price_24h_ago = close_price_by_hour.get(hour_start_24h_ago)
    if price_24h_ago and price_24h_ago != 0:
        return (mark_price - price_24h_ago) / price_24h_ago * 100
    return None


async def get_top5_funding_rates(symbol: str) -> list[dict]:
    """Return the 5 lowest 8h-normalized funding rate records for `symbol`."""
    interval_map = await get_interval_hours_map()
    interval_hours = interval_map.get(symbol, DEFAULT_INTERVAL_HOURS)

    funding_limit = 730 * (24 // interval_hours)
    records = await binance_client.get_funding_rate_history(symbol, limit=funding_limit)

    # 가장 오래된 펀딩피 시각을 기준으로 hourly klines 범위 결정
    if records:
        oldest_funding_ms = min(r["fundingTime"] for r in records)
        # 24시간 전 가격도 필요하므로 25시간 앞당겨서 조회
        start_ms = oldest_funding_ms - 25 * 3600 * 1000
    else:
        start_ms = int(time.time() * 1000) - 2 * 365 * 24 * 3600 * 1000
    end_ms = int(time.time() * 1000)

    klines = await binance_client.get_hourly_klines(symbol, start_ms, end_ms)

    # Build hour -> close_price map
    close_price_by_hour: dict[int, float] = {}
    for k in klines:
        open_time_ms = int(k[0])
        close_price = float(k[4])
        close_price_by_hour[open_time_ms] = close_price

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
        change_pct = _get_change_pct(r["fundingTime"], mark_price, close_price_by_hour)
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
