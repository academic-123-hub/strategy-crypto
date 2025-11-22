from __future__ import annotations

from typing import Dict, Any

import requests
import pandas as pd


BINANCE_FUTURES_BASE = "https://fapi.binance.com"
BINANCE_FUTURES_DATA_BASE = "https://fapi.binance.com"


def _http_get(url: str, params: Dict[str, Any] | None = None):
    """Wrapper simples para GET com timeout e tratamento básico."""
    resp = requests.get(url, params=params or {}, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_klines(symbol: str, interval: str = "1h", limit: int = 24) -> pd.DataFrame:
    """Retorna candles da Binance Futures em um DataFrame."""
    url = f"{BINANCE_FUTURES_BASE}/fapi/v1/klines"
    data = _http_get(url, params={"symbol": symbol, "interval": interval, "limit": limit})

    cols = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base",
        "taker_buy_quote",
        "ignore",
    ]
    df = pd.DataFrame(data, columns=cols)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
    df[["open", "high", "low", "close", "volume"]] = df[
        ["open", "high", "low", "close", "volume"]
    ].astype(float)
    return df


def get_price_change_pct(symbol: str, lookback_hours: int = 24) -> float:
    """
    Variação percentual do preço de fechamento no período
    (último close vs primeiro close).
    """
    # Usa 1h como padrão: N candles ≈ lookback_hours
    limit = max(2, lookback_hours)
    df = get_klines(symbol, interval="1h", limit=limit)
    first_close = df["close"].iloc[0]
    last_close = df["close"].iloc[-1]
    return (last_close - first_close) / first_close


def get_open_interest_series(symbol: str, period: str = "4h", limit: int = 2) -> pd.DataFrame:
    """Retorna série histórica de Open Interest agregado da Binance Futures."""
    url = f"{BINANCE_FUTURES_DATA_BASE}/futures/data/openInterestHist"
    params = {
        "symbol": symbol,
        "period": period,
        "limit": limit,
        "contractType": "PERPETUAL",
    }
    data = _http_get(url, params=params)
    df = pd.DataFrame(data)
    # campo 'sumOpenInterest' vem como string
    df["sumOpenInterest"] = df["sumOpenInterest"].astype(float)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    return df


def get_open_interest_change_pct(symbol: str, period: str = "4h") -> float:
    """Variação percentual do OI entre as duas últimas observações disponíveis."""
    df = get_open_interest_series(symbol, period=period, limit=2)
    if len(df) < 2:
        return 0.0
    prev_oi = df["sumOpenInterest"].iloc[-2]
    last_oi = df["sumOpenInterest"].iloc[-1]
    if prev_oi == 0:
        return 0.0
    return (last_oi - prev_oi) / prev_oi


def get_latest_funding_rate(symbol: str) -> float:
    """Retorna a última funding rate conhecida para o símbolo (como número decimal)."""
    url = f"{BINANCE_FUTURES_BASE}/fapi/v1/fundingRate"
    data = _http_get(url, params={"symbol": symbol, "limit": 1})
    if not data:
        return 0.0
    # fundingRate vem como string, exemplo '0.0001'
    return float(data[0]["fundingRate"])
