from __future__ import annotations

import time
from datetime import datetime, timezone, timedelta
from services import binance_client
from services.funding_service import (
    get_interval_hours_map,
    normalize_to_8h,
    DEFAULT_INTERVAL_HOURS,
    _infer_interval_hours,
    _hour_start_ms,
    _get_change_pct,
)


KST = timezone(timedelta(hours=9))

def _fmt_time(ts_ms: int) -> str:
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).astimezone(KST)
    return dt.strftime("%Y-%m-%d")


async def get_top5_price_surge_funding(symbol: str) -> list[dict]:
    """
    Find the 5 funding rate records with the highest 24h price increase for `symbol`.

    For each funding rate record, computes the price change over the 24 hours
    immediately preceding that funding time (markPrice vs hourly close 24h ago).
    Returns the top 5 by that metric, with the associated funding rate info.
    """
    interval_map = await get_interval_hours_map()
    interval_hours = interval_map.get(symbol, DEFAULT_INTERVAL_HOURS)

    funding_limit = 730 * (24 // interval_hours)
    funding_records = await binance_client.get_funding_rate_history(symbol, limit=funding_limit)

    if not funding_records:
        return []

    # 가장 오래된 펀딩피 시각을 기준으로 hourly klines 범위 결정
    oldest_funding_ms = min(r["fundingTime"] for r in funding_records)
    start_ms = oldest_funding_ms - 25 * 3600 * 1000
    end_ms = int(time.time() * 1000)

    klines = await binance_client.get_hourly_klines(symbol, start_ms, end_ms)

    # Build hour -> close_price map
    close_price_by_hour: dict[int, float] = {}
    for k in klines:
        open_time_ms = int(k[0])
        close_price = float(k[4])
        close_price_by_hour[open_time_ms] = close_price

    # 각 레코드에 당시 interval 및 24h 상승률 계산
    enriched = []
    for i, r in enumerate(funding_records):
        rec_interval = interval_hours if i == 0 else _infer_interval_hours(funding_records[i - 1]["fundingTime"], r["fundingTime"])
        r["_interval"] = rec_interval

        mark_str = r.get("markPrice", "") or "0"
        try:
            mark_price = float(mark_str)
        except (ValueError, TypeError):
            mark_price = 0.0

        change_pct = _get_change_pct(r["fundingTime"], mark_price, close_price_by_hour)
        if change_pct is None:
            continue

        rate_str = r.get("fundingRate", "") or "0"
        try:
            raw_rate = float(rate_str)
        except (ValueError, TypeError):
            continue

        normalized = normalize_to_8h(raw_rate, rec_interval)
        enriched.append({
            "date": _fmt_time(r["fundingTime"]),
            "fundingTime": r["fundingTime"],
            "changePct": change_pct,
            "rawRate": raw_rate,
            "normalizedRate8h": normalized,
            "intervalHours": rec_interval,
        })

    # 24h 상승률 기준 내림차순 정렬 후 top5
    enriched.sort(key=lambda x: x["changePct"], reverse=True)
    top5 = enriched[:5]

    return [
        {
            "date": item["date"],
            "changePct": round(item["changePct"], 4),
            "fundingTime": item["fundingTime"],
            "rawRate": round(item["rawRate"] * 100, 6),
            "normalizedRate8h": round(item["normalizedRate8h"] * 100, 6),
            "intervalHours": item["intervalHours"],
        }
        for item in top5
    ]
