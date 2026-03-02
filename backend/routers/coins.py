from fastapi import APIRouter, HTTPException
from services import binance_client

router = APIRouter()


@router.get("/coins")
async def list_coins():
    """Return all active USDT-margined perpetual futures symbols."""
    try:
        info = await binance_client.get_exchange_info()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Binance API error: {e}")

    symbols = [
        s["symbol"]
        for s in info.get("symbols", [])
        if s.get("contractType") == "PERPETUAL"
        and s.get("quoteAsset") == "USDT"
        and s.get("status") == "TRADING"
    ]
    symbols.sort()
    return {"symbols": symbols}
