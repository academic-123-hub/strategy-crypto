from .enums import (
    PriceTrend,
    OIState,
    FundingState,
    CVDState,
    LiquidationState,
)


def classify_price_trend(pct_change: float) -> PriceTrend:
    """Classifica tendência de preço a partir da variação percentual."""
    if pct_change > 0.03:
        return PriceTrend.FORTE_ALTA
    elif pct_change > 0.01:
        return PriceTrend.ALTA
    elif pct_change < -0.03:
        return PriceTrend.FORTE_BAIXA
    elif pct_change < -0.01:
        return PriceTrend.BAIXA
    else:
        return PriceTrend.LATERAL


def classify_oi_state(oi_pct_change: float) -> OIState:
    """Classifica o estado do OI pela variação percentual."""
    if oi_pct_change < -0.10:
        return OIState.QUEDA_FORTE
    elif oi_pct_change < -0.03:
        return OIState.QUEDA_MODERADA
    elif oi_pct_change <= 0.03:
        return OIState.ESTAVEL
    elif oi_pct_change <= 0.10:
        return OIState.ALTA_MODERADA
    else:
        return OIState.ALTA_FORTE


def classify_funding_state(funding: float) -> FundingState:
    """Classifica o estado do funding rate."""
    if funding < -0.0002:
        return FundingState.MUITO_NEGATIVO
    elif funding < -0.00005:
        return FundingState.NEGATIVO
    elif funding <= 0.00005:
        return FundingState.NEUTRO
    elif funding <= 0.0002:
        return FundingState.POSITIVO
    else:
        return FundingState.MUITO_POSITIVO


def classify_cvd_state(delta_cvd_rel: float) -> CVDState:
    """Classifica o fluxo agressor (CVD) relativo ao volume total."""
    if delta_cvd_rel < -0.20:
        return CVDState.VENDA_FORTE
    elif delta_cvd_rel < -0.05:
        return CVDState.VENDA_MODERADA
    elif delta_cvd_rel <= 0.05:
        return CVDState.NEUTRO
    elif delta_cvd_rel <= 0.20:
        return CVDState.COMPRA_MODERADA
    else:
        return CVDState.COMPRA_FORTE


def classify_liquidation_state(
    long_liq_z: float, short_liq_z: float
) -> LiquidationState:
    """
    Classifica o estado das liquidações com base em z-score
    (desvio em relação à média histórica).
    """
    # z = (volume_liq - média) / desvio_padrão

    if long_liq_z < 1 and short_liq_z < 1:
        return LiquidationState.BAIXO

    # moderado
    if 1 <= long_liq_z < 2 or 1 <= short_liq_z < 2:
        return LiquidationState.MODERADO

    # altos
    if 2 <= long_liq_z < 3 and long_liq_z > short_liq_z:
        return LiquidationState.ALTO_LONGS
    if 2 <= short_liq_z < 3 and short_liq_z > long_liq_z:
        return LiquidationState.ALTO_SHORTS

    # capitulação
    if long_liq_z >= 3 and long_liq_z > short_liq_z:
        return LiquidationState.CAPITULACAO_LONGS
    if short_liq_z >= 3 and short_liq_z > long_liq_z:
        return LiquidationState.CAPITULACAO_SHORTS

    return LiquidationState.MODERADO
