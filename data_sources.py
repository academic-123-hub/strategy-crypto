from __future__ import annotations

from typing import Dict, Any

import requests
import pandas as pd


BINANCE_FUTURES_BASE = "https://fapi.binance.com"
BINANCE_FUTURES_DATA_BASE = "https://fapi.binance.com"
BINANCE_SPOT_BASE = "https://api.binance.com"


class BinanceRestrictedError(RuntimeError):
    """Erro para indicar restrição legal (HTTP 451 / 403) ao acessar Binance."""
    pass


def _http_get(url: str, params: Dict[str, Any] | None = None):
    """Wrapper simples para GET com timeout e tratamento básico."""
    resp = requests.get(url, params=params or {}, timeout=10)
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        # Se for 451/403, levantamos erro específico para tratar fallback
        if resp.status_code in (451, 403):
            raise BinanceRestrictedError(
                f"Acesso restrito pela Binance ({resp.status_code}) em {url}"
            ) from exc
        raise
    return resp.json()


def get_klines(symbol: str, interval: str = "1h", limit: int = 24) -> pd.DataFrame:
    """
    Retorna candles em um DataFrame.

    1ª tentativa: Binance Futures (fapi).
    Se der restrição legal (451/403), cai para Binance Spot (api).
    """
    params = {"symbol": symbol, "interval": interval, "limit": limit}

    try:
        url = f"{BINANCE_FUTURES_BASE}/fapi/v1/klines"
        data = _http_get(url, params=params)
    except BinanceRestrictedError:
        # Fallback: usa klines do mercado Spot (formato é compatível)
        url = f"{BINANCE_SPOT_BASE}/api/v3/klines"
        data = _http_get(url, params=params)

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


def get_open_interest_series(
    symbol: str, period: str = "4h", limit: int = 2
) -> pd.DataFrame:
    """Retorna série histórica de Open Interest agregado da Binance Futures.

    Em hosts com restrição legal (451/403), retorna DataFrame vazio.
    """
    url = f"{BINANCE_FUTURES_DATA_BASE}/futures/data/openInterestHist"
    params = {
        "symbol": symbol,
        "period": period,
        "limit": limit,
        "contractType": "PERPETUAL",
    }
    try:
        data = _http_get(url, params=params)
    except BinanceRestrictedError:
        # No Streamlit Cloud (ou regiões bloqueadas), OI pode não estar disponível
        return pd.DataFrame(columns=["timestamp", "sumOpenInterest"])

    df = pd.DataFrame(data)
    if df.empty:
        return df
    df["sumOpenInterest"] = df["sumOpenInterest"].astype(float)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    return df


def get_open_interest_change_pct(symbol: str, period: str = "4h") -> float:
    """Variação percentual do OI entre as duas últimas observações disponíveis.

    Se OI não estiver disponível (restrição legal), retorna 0.0.
    """
    df = get_open_interest_series(symbol, period=period, limit=2)
    if df is None or len(df) < 2:
        return 0.0
    prev_oi = df["sumOpenInterest"].iloc[-2]
    last_oi = df["sumOpenInterest"].iloc[-1]
    if prev_oi == 0:
        return 0.0
    return (last_oi - prev_oi) / prev_oi


def get_latest_funding_rate(symbol: str) -> float:
    """
    Retorna a última funding rate conhecida para o símbolo (como número decimal).

    Se houver restrição legal para acessar a Binance Futures no host,
    retorna 0.0.
    """
    url = f"{BINANCE_FUTURES_BASE}/fapi/v1/fundingRate"
    params = {"symbol": symbol, "limit": 1}
    try:
        data = _http_get(url, params=params)
    except BinanceRestrictedError:
        return 0.0

    if not data:
        return 0.0
    return float(data[0]["fundingRate"])
