from .enums import (
    PriceTrend,
    OIState,
    FundingState,
    CVDState,
    LiquidationState,
    MarketContext,
)


def infer_market_context(
    price_trend: PriceTrend,
    oi_state: OIState,
    funding_state: FundingState,
    cvd_state: CVDState,
    liq_state: LiquidationState,
) -> MarketContext:
    """Aplica o motor de regras para inferir o contexto de mercado."""

    # 1) Alta saudável
    if price_trend in (PriceTrend.ALTA, PriceTrend.FORTE_ALTA):
        if oi_state in (OIState.ALTA_MODERADA, OIState.ALTA_FORTE):
            if funding_state in (FundingState.NEUTRO, FundingState.POSITIVO):
                if cvd_state in (CVDState.COMPRA_MODERADA, CVDState.COMPRA_FORTE):
                    if liq_state in (LiquidationState.BAIXO, LiquidationState.MODERADO):
                        return MarketContext.ALTA_SAUDAVEL

    # 2) Alta eufórica / risco de topo
    if price_trend in (PriceTrend.ALTA, PriceTrend.FORTE_ALTA):
        if oi_state == OIState.ALTA_FORTE:
            if funding_state == FundingState.MUITO_POSITIVO:
                if cvd_state in (CVDState.NEUTRO, CVDState.COMPRA_MODERADA):
                    return MarketContext.ALTA_EUFORICA_RISCO_TOPO

    # 3) Alta por short squeeze
    if price_trend in (PriceTrend.ALTA, PriceTrend.FORTE_ALTA):
        if liq_state in (LiquidationState.ALTO_SHORTS, LiquidationState.CAPITULACAO_SHORTS):
            if funding_state in (FundingState.POSITIVO, FundingState.MUITO_POSITIVO):
                return MarketContext.ALTA_SHORT_SQUEEZE

    # 4) Queda com correção saudável
    if price_trend in (PriceTrend.BAIXA, PriceTrend.FORTE_BAIXA):
        if oi_state in (OIState.QUEDA_MODERADA, OIState.ESTAVEL):
            if funding_state in (FundingState.NEUTRO, FundingState.NEGATIVO):
                if liq_state in (LiquidationState.BAIXO, LiquidationState.MODERADO):
                    return MarketContext.QUEDA_CORRECAO_SAUDAVEL

    # 5) Queda com capitulação / risco de fundo
    if price_trend in (PriceTrend.BAIXA, PriceTrend.FORTE_BAIXA):
        if oi_state in (OIState.QUEDA_FORTE, OIState.QUEDA_MODERADA):
            if funding_state in (FundingState.NEGATIVO, FundingState.MUITO_NEGATIVO):
                if liq_state in (LiquidationState.ALTO_LONGS, LiquidationState.CAPITULACAO_LONGS):
                    return MarketContext.QUEDA_CAPITULACAO_RISCO_FUNDO

    # 6) Range com baixa alavancagem
    if price_trend == PriceTrend.LATERAL:
        if oi_state in (OIState.QUEDA_MODERADA, OIState.ESTAVEL):
            if funding_state in (FundingState.NEUTRO,):
                return MarketContext.RANGE_BAIXA_ALAVANCAGEM

    # 7) Range com alta alavancagem / risco de squeeze
    if price_trend == PriceTrend.LATERAL:
        if oi_state in (OIState.ALTA_MODERADA, OIState.ALTA_FORTE):
            if funding_state in (FundingState.POSITIVO, FundingState.NEGATIVO):
                return MarketContext.RANGE_ALTA_ALAVANCAGEM_RISCO_SQUEEZE

    # Fallback
    return MarketContext.INDEFINIDO
