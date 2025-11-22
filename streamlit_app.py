import streamlit as st

from core.enums import (
    MarketContext,
    CVDState,
    LiquidationState,
)
from core.classifiers import (
    classify_price_trend,
    classify_oi_state,
    classify_funding_state,
)
from core.context_engine import infer_market_context
from core.data_sources import (
    get_price_change_pct,
    get_open_interest_change_pct,
    get_latest_funding_rate,
)


SYMBOL = "BTCUSDT"


def market_context_description(context: MarketContext) -> str:
    """Descrição amigável para cada contexto de mercado."""
    if context == MarketContext.ALTA_SAUDAVEL:
        return "Alta saudável: tendência de alta com alavancagem e fluxo compatíveis."
    if context == MarketContext.ALTA_EUFORICA_RISCO_TOPO:
        return "Alta eufórica: muita alavancagem compradora, risco elevado de topo/local."
    if context == MarketContext.ALTA_SHORT_SQUEEZE:
        return "Alta impulsionada por short squeeze: movimento forçado contra vendidos."
    if context == MarketContext.QUEDA_CORRECAO_SAUDAVEL:
        return "Queda/correção saudável dentro de uma estrutura de mercado ainda equilibrada."
    if context == MarketContext.QUEDA_CAPITULACAO_RISCO_FUNDO:
        return "Queda com capitulação: flush forte de comprados, possível zona de fundo (com cautela)."
    if context == MarketContext.RANGE_BAIXA_ALAVANCAGEM:
        return "Mercado em range com baixa alavancagem: contexto mais neutro e menos explosivo."
    if context == MarketContext.RANGE_ALTA_ALAVANCAGEM_RISCO_SQUEEZE:
        return "Range com alta alavancagem: atenção a possíveis squeezes para qualquer lado."
    return "Contexto de mercado indefinido ou misto."


def main() -> None:
    st.set_page_config(
        page_title="Market Context – BTCUSDT",
        page_icon="📊",
        layout="wide",
    )

    st.title("📊 Market Context – BTCUSDT (Binance Futures)")
    st.caption(
        "Leitura automática de contexto usando Preço, Open Interest e Funding da Binance Futures."
    )

    col_left, col_right = st.columns([2, 1])

    # Sidebar com parâmetros simples
    with st.sidebar:
        st.header("Parâmetros")
        lookback_hours = st.slider(
            "Janela para tendência de preço (horas)",
            min_value=4,
            max_value=72,
            value=24,
            step=4,
        )
        oi_period = st.selectbox(
            "Período para variação de OI",
            options=["1h", "4h", "8h", "12h", "24h"],
            index=1,
            help="Período dos pontos usados para calcular a variação percentual de OI.",
        )

    # Coluna esquerda: dados brutos
    with col_left:
        st.subheader("Dados brutos (BTCUSDT Perp – Binance Futures)")

        try:
            price_pct_change = get_price_change_pct(SYMBOL, lookback_hours=lookback_hours)
            oi_pct_change = get_open_interest_change_pct(SYMBOL, period=oi_period)
            funding_rate = get_latest_funding_rate(SYMBOL)
        except Exception as exc:
            st.error(f"Erro ao buscar dados da Binance: {exc}")
            return

        m1, m2, m3 = st.columns(3)
        m1.metric(
            "Variação de preço",
            f"{price_pct_change * 100:.2f} %",
            help=f"Últimas {lookback_hours}h (fechamento vs primeiro candle).",
        )
        m2.metric(
            "Variação de OI",
            f"{oi_pct_change * 100:.2f} %",
            help=f"Variação percentual entre as duas últimas observações de OI ({oi_period}).",
        )
        m3.metric(
            "Funding rate",
            f"{funding_rate * 100:.4f} %",
            help="Última funding rate disponível na Binance Futures.",
        )

    # Coluna direita: contexto
    with col_right:
        st.subheader("Contexto de Mercado")

        # Classificação dos estados
        price_trend = classify_price_trend(price_pct_change)
        oi_state = classify_oi_state(oi_pct_change)
        funding_state = classify_funding_state(funding_rate)

        # Versão inicial: ainda não calculamos CVD e liquidações → assumimos neutros/moderados
        cvd_state = CVDState.NEUTRO
        liq_state = LiquidationState.MODERADO

        context = infer_market_context(
            price_trend=price_trend,
            oi_state=oi_state,
            funding_state=funding_state,
            cvd_state=cvd_state,
            liq_state=liq_state,
        )

        st.markdown(f"### 🧠 MarketContext: `{context.name}`")
        st.write(market_context_description(context))

        with st.expander("Ver classificação detalhada"):
            st.write("**Tendência de Preço:**", price_trend.name)
            st.write("**Estado do OI:**", oi_state.name)
            st.write("**Estado do Funding:**", funding_state.name)
            st.write("**Fluxo (CVD):**", cvd_state.name, "(assumido)")
            st.write("**Liquidações:**", liq_state.name, "(assumido)")

    st.markdown("---")
    st.caption(
        "Protótipo inicial – próximos passos: inclusão de CVD real, liquidações, comparação multi-timeframe, etc."
    )


if __name__ == "__main__":
    main()
